from extensions.kudos.manager import KudosManager
from extensions.mods.mod_manager import ModManager
from discord import Guild, Member, Message, TextChannel, utils
from datetime import datetime, timedelta, timezone
from typing import Optional
import asyncio
import dippy.labels
import dippy


class VoiceChatExtension(dippy.Extension):
    client: dippy.Client
    kudos: KudosManager
    labels: dippy.labels.storage.StorageInterface
    mod_manager: ModManager

    @dippy.Extension.listener("ready")
    async def fix_joins(self):
        results = await self.labels.find("member[644299523686006834]", key="joined")
        guild = self.client.get_guild(644299523686006834)
        start = datetime.now().astimezone(timezone.utc) - timedelta(hours=1, minutes=10)
        end = start + timedelta(minutes=40)
        new_member = guild.get_role(888160821673349140)
        suspended = guild.get_role(856200823854989372)
        for label in results:
            member = guild.get_member(label.id)
            if not member:
                continue
            if not isinstance(label.value, str):
                print("Not a string:", repr(label.value))
                continue
            if (
                start <= datetime.fromisoformat(label.value) <= end
                and new_member in member.roles
            ):
                print(f"Suspending {member}")
                await member.add_roles(suspended)
                await member.remove_roles(new_member)

    @dippy.Extension.listener("ready")
    async def onboard_new_members(self):
        guild = self.client.get_guild(644299523686006834)
        role = guild.get_role(888160821673349140)
        for member in role.members:
            try:
                joined_time = await member.get_label("joined")
                joined = datetime.fromisoformat(joined_time)
                await self.schedule_onboarding(member, joined)
            except TypeError:
                print(
                    f"{datetime.utcnow().isoformat()} FAILED TO GET JOINED TIME {joined_time!r}"
                )

    @dippy.Extension.listener("ready")
    async def assign_missing_roles(self):
        guild = self.client.get_guild(644299523686006834)
        need_roles = []
        for member in guild.members:
            if len(member.roles) < 2:
                need_roles.append(self.onboard_member(member))

        if need_roles:
            await asyncio.gather(*need_roles)
            await guild.get_channel(865010559861522442).send(
                f"Restarted and added roles to {len(need_roles)} members"
            )

    @dippy.Extension.command("!set welcome channel")
    async def set_welcome_channel(self, message: Message):
        if not message.author.guild_permissions.manage_channels:
            return

        await self.labels.set(
            "guild",
            message.guild.id,
            "welcome_channel_id",
            message.channel_mentions[0].id,
        )

    @dippy.Extension.listener("member_update")
    async def member_accepts_rules(self, before: Member, after: Member):
        if before.pending and not after.pending:
            await asyncio.gather(
                self.add_unwelcomed_user(after),
                self.onboard_member(after),
                self.check_for_highscore(after.guild),
            )

    async def check_for_highscore(self, guild: Guild):
        if await self.mod_manager.locked_down(guild):
            return

        last_highest = await guild.get_label("highest-member-count", default=0)
        count = self.get_num_members(guild)
        if count > last_highest or last_highest - count > 200:
            await guild.set_label("highest-member-count", count)
            if count // 100 > last_highest // 100:
                await guild.get_channel(644299524151443487).send(
                    f"🎉🥳🎈 We've reached {count // 100 * 100} members!!! 🎈🥳🎉"
                )

    async def onboard_member(self, member: Member):
        await member.add_roles(member.guild.get_role(888160821673349140))
        joined = datetime.now().astimezone(timezone.utc)
        await member.set_label("joined", joined.isoformat())
        await self.schedule_onboarding(member, joined)

    async def schedule_onboarding(self, member: Member, joined: datetime):
        async def onboard():
            try:
                await member.add_roles(member.guild.get_role(644325811301777426))
            except:
                pass
            else:
                await member.remove_roles(member.guild.get_role(888160821673349140))

        now = datetime.now().astimezone(timezone.utc)
        when = joined + timedelta(days=2)
        if when <= now:
            await onboard()
        else:
            asyncio.get_running_loop().call_later(
                (when - now).total_seconds(),
                lambda: asyncio.get_running_loop().create_task(onboard()),
            )

    def get_num_members(self, guild: Guild) -> int:
        return sum(1 for member in guild.members if not member.bot)

    @dippy.Extension.listener("message")
    async def welcome_messages(self, message: Message):
        if message.author.bot or not isinstance(message.channel, TextChannel):
            return

        channel = await self.get_welcome_channel(message.guild)
        if message.channel != channel:
            return

        unwelcomed_members = await self.get_unwelcomed_users(message.guild)
        if not unwelcomed_members or message.author in unwelcomed_members:
            return

        await self._give_kudos_for_welcoming(
            message.author, len(unwelcomed_members), channel
        )

    async def get_welcome_channel(self, guild: Guild) -> Optional[TextChannel]:
        channel_id = await self.labels.get("guild", guild.id, "welcome_channel_id")
        return channel_id and guild.get_channel(channel_id)

    async def get_unwelcomed_users(self, guild: Guild) -> list[Member]:
        return [
            guild.get_member(member_id)
            for member_id in await self.labels.get(
                "guild", guild.id, "unwelcomed_members", []
            )
        ]

    async def add_unwelcomed_user(self, member: Member):
        if member.id == 335491211039080458:
            return  # Ignore dev alt

        unwelcomed = await self.get_unwelcomed_users(member.guild)
        unwelcomed.append(member)
        await self._set_unwelcomed_users(member.guild, unwelcomed)

    async def clear_unwelcomed_users(self, guild: Guild):
        await self._set_unwelcomed_users(guild, [])

    async def _give_kudos_for_welcoming(
        self, member: Member, num_welcomed: int, channel: TextChannel
    ):
        kudos = 2 * num_welcomed
        await self.clear_unwelcomed_users(member.guild)
        await self.kudos.give_kudos(
            member,
            kudos,
            f"{member.mention} welcomed {num_welcomed} member{'s' * (num_welcomed > 1)} to the server!!!",
        )
        expert_emoji = utils.get(member.guild.emojis, name="expert")
        await channel.send(
            f"{expert_emoji} {member.mention} you got {kudos} kudos for welcoming {num_welcomed} "
            f"member{'s' * (num_welcomed > 1)}!",
            delete_after=60,
        )

    async def _set_unwelcomed_users(self, guild: Guild, unwelcomed: list[Member]):
        await self.labels.set(
            "guild",
            guild.id,
            "unwelcomed_members",
            [member.id for member in unwelcomed if member],
        )
