from datetime import datetime, timedelta, timezone
from nextcord import (
    AuditLogAction,
    Embed,
    Guild,
    Member,
    Message,
    utils,
    Permissions,
    AllowedMentions,
)
from extensions.user_tracking.manager import UserTracker
from extensions.mods.mod_settings import ModSettingsExtension
from extensions.mods.mod_manager import ModManager
import dippy
import dippy.labels
import re
import random


class ModeratorsExtension(dippy.Extension):
    client: dippy.Client
    user_tracking: UserTracker
    labels: dippy.labels.storage.StorageInterface
    settings: ModSettingsExtension
    mod_manager: ModManager

    @dippy.Extension.listener("ready")
    async def on_ready(self):
        self.client.remove_command("help")

    @dippy.Extension.command("!lockdown")
    async def lockdown(self, message: Message):
        if not message.author.guild_permissions.manage_messages:
            return

        if "lift" in message.content.strip().casefold():
            await self.mod_manager.lift_lockdown(message.guild, message.channel)
        else:
            await self.mod_manager.lockdown(message.guild, message.channel)

    @dippy.Extension.command("!mass ban")
    async def mass_ban(self, message: Message):
        if not message.author.guild_permissions.manage_messages:
            return

        alerting = await self.mod_manager.alert_active(message.guild)
        if alerting == -1:
            await message.channel.send("No alerts active. Mass ban is disabled.")
            return

        now = datetime.utcnow().astimezone(timezone.utc)
        start = now - timedelta(minutes=alerting)
        try:
            duration = int(message.content.rpartition(" ")[-1].strip())
        except ValueError:
            end = now
        else:
            end = start + timedelta(minutes=duration)

        await message.channel.send(
            f"Banning all members who joined from <t:{start.timestamp():.0f}:t> until <t:{end.timestamp():.0f}:t>"
        )
        num_banned = await self.mod_manager.mass_ban(message.guild, start, end)
        await message.channel.send(f"Banned {num_banned} members")

    @dippy.Extension.command("!bans")
    async def bans(self, message: Message):
        num_bans = len(await message.guild.bans())
        await message.channel.send(f"Found {num_bans} banned members")

    @dippy.Extension.command("!team")
    async def team_command(self, message: Message):
        boosters = utils.get(message.guild.roles, name="Discord Boosters!!!").members
        helpers = list(utils.get(message.guild.roles, name="helpers").members)
        mods = utils.get(message.guild.roles, name="mods").members
        staff = utils.get(message.guild.roles, name="staff").members

        random.shuffle(helpers)

        owner = message.guild.owner
        wolf_wave_emoji = utils.get(message.guild.emojis, name="wolfwave")
        embed = (
            Embed(
                title="Beginner.Codes Team",
                description=(
                    "Hi! The Beginner.Codes team is dedicated to maintaining a friendly environment where everyone can "
                    "learn."
                ),
                color=0x00A35A,
            )
            .add_field(
                name="🤴Server Owner", value=f"`{owner.display_name}`", inline=False
            )
            .add_field(
                name="👮Moderators",
                value=", ".join(
                    f"`{mod.display_name}`" for mod in mods if mod != owner
                ),
                inline=False,
            )
            .add_field(
                name="👷Staff",
                value=", ".join(
                    f"`{member.display_name}`" for member in staff if member not in mods
                ),
                inline=False,
            )
            .add_field(
                name="🙋Volunteer Helpers",
                value=", ".join(
                    f"`{member.display_name}`"
                    for member in sorted(
                        helpers[:10], key=lambda m: m.display_name.casefold()
                    )
                    if member not in mods
                )
                + (f", & {len(helpers) - 10} others" if len(helpers) > 10 else ""),
                inline=False,
            )
            .set_thumbnail(url=wolf_wave_emoji.url)
        )
        if boosters:
            embed.add_field(
                name="✨Discord Boosters!!!",
                value=", ".join(f"`{booster.display_name}`" for booster in boosters),
                inline=False,
            )
        await message.reply(embed=embed)

    @dippy.Extension.command("!!mute")
    async def mute_command(self, message: Message):
        if not message.guild or message.author.bot:
            return

        user_id, duration, units, reason = re.match(
            r"[^a-z]+mute <@.+?(\d+)>\s(\d+)([dhm]?)(?:ours|our|ays|ay|inutes|inute|in)?\s*(.*)",
            message.content,
        ).groups()

        mod_roles = await self.settings.get_mod_roles(message.guild)
        helper_roles = await self.settings.get_helper_roles(message.guild)
        roles = set(message.author.roles)
        if not mod_roles & roles and not helper_roles & roles:
            return

        member = message.guild.get_member(int(user_id))
        if not member:
            await message.channel.send("That user is no longer a member here")
            return

        if member.top_role.position >= message.author.top_role.position:
            await message.channel.send(
                f"{message.author.mention} you can't mute members with the {member.top_role.name} role"
            )
            return

        duration_settings = {
            {"d": "days", "h": "hours"}.get(units, "minutes"): int(duration)
        }
        time_duration = int(timedelta(**duration_settings).total_seconds())

        if mod_roles & roles:
            await self.mod_manager.mute(
                member,
                message.author,
                time_duration,
                message,
                reason or None,
            )
            await message.channel.send(
                f"Muted {member.mention} for {self.mod_manager.format_duration(time_duration)}"
            )

    @dippy.Extension.command("!count bans")
    async def cleanup_help_section(self, message: Message):
        if not message.author.guild_permissions.kick_members:
            return

        content = message.content.rpartition(" ")[-1].strip()
        days = timedelta(days=int(content) if content.isdigit() else 1)

        guild: Guild = message.guild
        bans = 0
        resp = await guild._state.http.get_audit_logs(
            guild.id, limit=100, action_type=AuditLogAction.ban.value
        )
        stop = utils.time_snowflake(datetime.utcnow() - days, high=True)
        bans += len(
            [1 for entry in resp["audit_log_entries"] if int(entry["id"]) > stop]
        )
        while (
            resp
            and resp["audit_log_entries"]
            and int(resp["audit_log_entries"][-1]["id"]) > stop
        ):
            resp = await guild._state.http.get_audit_logs(
                guild.id,
                limit=100,
                action_type=AuditLogAction.ban.value,
                before=int(resp["audit_log_entries"][-1]["id"]),
            )
            bans += len(
                [1 for entry in resp["audit_log_entries"] if int(entry["id"]) > stop]
            )

        num_days = days // timedelta(days=1)
        await message.channel.send(
            f"Found {bans} in the last {'day' if num_days == 1 else f'{num_days} days'}"
        )

    @dippy.Extension.command("!username history")
    async def show_username_history_command(self, message: Message):
        members: list[Member] = (
            [member for member in message.mentions if isinstance(member, Member)]
            or (await self._parse_members(message))
            or [message.author]
        )
        embed = Embed(
            title="Username History",
            description="Here are the username histories you requested.",
        )
        for member in members:
            history = await self.user_tracking.get_username_history(member)
            history_message = "*No name change history found*"
            if history:
                history_message = "\n".join(
                    f"{entry.date.strftime('%Y-%m-%d')} __{entry.old_username}__ to __{entry.new_username}__"
                    for entry in reversed(history)
                )
            title = str(member)  # Username with discriminator
            if member.nick:
                title = f"{title} ({member.display_name})"
            embed.add_field(name=title, value=history_message, inline=False)

        await message.channel.send(embed=embed)

    async def _parse_members(self, message: Message) -> list[Member]:
        members = []
        for section in message.content.strip().casefold().split():
            member = None
            if section.isdigit():
                member = message.guild.get_member(int(section))

            if not member:
                for guild_member in message.guild.members:
                    if guild_member.display_name.casefold() == section:
                        member = guild_member
                        break

            if member:
                members.append(member)

        return members
