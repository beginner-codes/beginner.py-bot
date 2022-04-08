from bevy import Injectable
from datetime import datetime, timedelta, timezone
from dippy import Client
from dippy.labels.storage import StorageInterface
from discord import (
    AllowedMentions,
    Embed,
    Guild,
    Member,
    Message,
    Permissions,
    TextChannel,
    HTTPException,
    Forbidden,
)
from extensions.mods.mod_settings import ModSettingsExtension
from typing import Optional
import asyncio


class ModManager(Injectable):
    client: Client
    settings: ModSettingsExtension
    labels: StorageInterface

    def __init__(self):
        self._next_mute_remove: Optional[datetime] = None
        self._mute_remove_future: Optional[asyncio.Future] = None

    @property
    def loop(self) -> asyncio.AbstractEventLoop:
        return asyncio.get_event_loop()

    async def alert_active(self, guild: Guild) -> int:
        started = await guild.get_label("alert_started", default=None)
        if not started:
            return -1

        started = datetime.fromisoformat(started)
        now = datetime.now().astimezone(timezone.utc)
        duration = (now - started) // timedelta(minutes=1)
        return duration if duration <= 30 else -1

    async def start_alert(self, guild: Guild):
        if (await self.alert_active(guild)) >= 0:
            return

        now = datetime.now().astimezone(timezone.utc) - timedelta(seconds=30)
        await guild.set_label("alert_started", now.isoformat())

    async def mass_ban(self, guild: Guild, start: datetime, end: datetime) -> int:
        count = 0
        log_channel = guild.get_channel(719311864479219813)
        for member in guild.members:
            print(start, member.joined_at, end)
            if start <= member.joined_at <= end:
                await member.ban(reason="Mass ban")
                await log_channel.send(f"Banned {member.display_name}")
                count += 1
        return count

    async def locked_down(self, guild: Guild) -> bool:
        return await guild.get_label("locked_down", default=False)

    async def lockdown(self, guild: Guild, channel: TextChannel):
        member_role = guild.get_role(644299523686006834)
        permissions = Permissions(
            send_messages=False,
            send_messages_in_threads=False,
            add_reactions=False,
            embed_links=False,
            attach_files=False,
            external_emojis=False,
            connect=False,
            speak=False,
            use_voice_activation=False,
            change_nickname=False,
            request_to_speak=False,
            external_stickers=False,
            read_messages=True,
            read_message_history=True,
        )
        await member_role.edit(permissions=permissions)
        await guild.set_label("locked_down", True)
        await self.start_alert(guild)
        await channel.send(
            f"🚨 Locked the server for {member_role} 🚨",
            allowed_mentions=AllowedMentions(roles=False, everyone=False),
        )

    async def lift_lockdown(self, guild: Guild, channel: TextChannel):
        member_role = guild.get_role(644299523686006834)
        permissions = Permissions(
            send_messages=True,
            send_messages_in_threads=True,
            add_reactions=True,
            embed_links=True,
            attach_files=True,
            external_emojis=True,
            connect=True,
            speak=True,
            use_voice_activation=True,
            change_nickname=True,
            request_to_speak=True,
            external_stickers=True,
            read_messages=True,
            read_message_history=True,
        )
        await member_role.edit(permissions=permissions)
        await guild.set_label("locked_down", False)
        await channel.send(
            f"Unlocked the server for {member_role}",
            allowed_mentions=AllowedMentions(roles=False, everyone=False),
        )

    async def mute(
        self,
        member: Member,
        mod: Member,
        duration: int,
        message: Message,
        reason: Optional[str] = None,
    ):
        mod_roles = await self.settings.get_mod_roles(member.guild)
        helper_roles = await self.settings.get_helper_roles(member.guild)
        roles = set(mod.roles)
        if mod_roles & roles:
            await self._mod_mute(member, mod, duration, message, reason)
        # elif helper_roles & roles:
        #     await self._helper_mute(member, mod, duration, reason)

    def set_next_unmute(self, time: datetime):
        if self._next_mute_remove and time >= self._next_mute_remove:
            return

        if self._mute_remove_future:
            self._mute_remove_future.cancel()

        self._mute_remove_future = self.loop.create_task(self._remove_mutes(time))
        self._next_mute_remove = time

    async def _get_reason(self, mod: Member) -> Optional[str]:
        def check(m: Message) -> bool:
            return m.content.startswith("!reason") and m.author == mod

        try:
            message = await self.client.wait_for("message", check=check, timeout=60)
        except asyncio.TimeoutError:
            return
        else:
            return message.content.partition(" ")[-1]

    async def _mute(self, member: Member, duration: int):
        unmute_time = datetime.utcnow() + timedelta(seconds=duration)
        await member.add_roles(await self.settings.get_mute_role(member.guild))
        await member.set_label("muted-until", unmute_time.isoformat())
        self.set_next_unmute(unmute_time)

    async def _mod_mute(
        self,
        member: Member,
        mod: Member,
        duration: int,
        message: Message,
        reason: Optional[str] = None,
    ):
        ends = datetime.utcnow() + timedelta(seconds=duration)
        await self._mute(member, duration)
        if not reason:
            reason = await self._get_reason(mod)

        await self._dm_user(member, "muted", duration, reason)

        formatted_duration = self.format_duration(duration)
        action_description = (
            f"{mod.mention} ({mod}) has muted {member.mention} ({member})\n**Duration**: {formatted_duration} "
            f"({ends.isoformat()} UTC)"
        )
        if reason:
            formatted_reason = "\n> ".join(reason.split("\n"))
            action_description += f"\n> {formatted_reason}"

        await self._log_action(
            member,
            mod,
            "Muted",
            action_description,
            message,
            0xFF0088,
        )

    async def _dm_user(
        self, member: Member, action: str, duration: int, reason: Optional[str]
    ):
        when = datetime.utcnow() + timedelta(seconds=duration)
        mute_message = (
            f"You've been muted on the {member.guild.name} server for {self.format_duration(duration)} "
            f"({when.isoformat()} UTC)."
        )
        if reason:
            mute_message += f"\n\n{reason}"
        try:
            await member.send(mute_message)
        except (HTTPException, Forbidden):
            pass

    async def _log_action(
        self,
        member: Member,
        mod: Member,
        title: str,
        description: str,
        message: Message,
        color: int = 0xFF0000,
    ):
        log = await self.settings.get_mod_log_channel(member.guild)
        await log.send(
            embed=Embed(
                title=f"Mod {mod}: {title.title()} - {member}",
                description=description,
                color=color,
                url=message.jump_url,
                timestamp=datetime.utcnow(),
            )
        )

    async def _remove_mutes(self, time: datetime):
        if time > datetime.utcnow():
            await asyncio.sleep((time - datetime.utcnow()).total_seconds())

        now = datetime.utcnow()
        next_check = None
        for mute_until_label in await self.labels.find(key="muted-until"):
            time = datetime.fromisoformat(mute_until_label.value)
            if time <= now:
                guild = self.client.get_guild(int(mute_until_label.type[7:-1]))
                member = guild.get_member(mute_until_label.id)
                await member.remove_roles(await self.settings.get_mute_role(guild))
                await self.labels.delete(
                    mute_until_label.type, mute_until_label.id, mute_until_label.key
                )
            elif not next_check or next_check > time - now:
                next_check = time - now

        if next_check:
            self.set_next_unmute(now + next_check)
        else:
            self._next_mute_remove = None
            self._mute_remove_future = None

    def format_duration(self, duration: int):
        sections = []
        remaining = timedelta(seconds=duration)
        for name, mod in zip(
            ("day", "hour", "minute"),
            (timedelta(days=1), timedelta(hours=1), timedelta(minutes=1)),
        ):
            total, remaining = divmod(remaining, mod)
            if total:
                sections.append(f"{total} {name + ('s' * (total != 1))}")

        return ", ".join(sections) if sections else "Now"
