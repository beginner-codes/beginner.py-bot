from datetime import datetime, timedelta
from discord import AuditLogAction, Embed, Guild, Member, Message, utils
from extensions.user_tracking.manager import UserTracker
from extensions.mods.mod_settings import ModSettingsExtension
from extensions.mods.mod_manager import ModManager
import dippy
import dippy.labels
import re


class ModeratorsExtension(dippy.Extension):
    client: dippy.Client
    user_tracking: UserTracker
    labels: dippy.labels.storage.StorageInterface
    settings: ModSettingsExtension
    mod_manager: ModManager

    @dippy.Extension.listener("ready")
    async def on_ready(self):
        self.client.remove_command("help")

    @dippy.Extension.command("!team")
    async def team_command(self, message: Message):
        helpers = utils.get(message.guild.roles, name="helpers").members
        mods = utils.get(message.guild.roles, name="mods").members
        boosters = utils.get(message.guild.roles, name="Discord Boosters!!!").members
        wolf_wave_emoji = utils.get(message.guild.emojis, name="wolfwave")
        owner = max(mods, key=message.guild.owner.__eq__)
        embed = (
            Embed(
                title="Beginner.py Team",
                description=(
                    "Hi! The Beginner.py team is dedicated to maintaining a friendly environment where everyone can "
                    "learn."
                ),
                color=0x00A35A,
            )
            .add_field(name="🤴Server Owner", value=owner.mention, inline=False)
            .add_field(
                name="👮Moderators",
                value=", ".join(mod.mention for mod in mods if mod != owner),
                inline=False,
            )
            .add_field(
                name="👷Helpers",
                value=", ".join(
                    helper.mention for helper in helpers if helper not in mods
                ),
                inline=False,
            )
            .set_thumbnail(url=wolf_wave_emoji.url)
        )
        if boosters:
            embed.add_field(
                name="✨Discord Boosters!!!",
                value=", ".join(booster.mention for booster in boosters),
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

        guild: Guild = message.guild
        bans = await guild.audit_logs(
            action=AuditLogAction.ban, after=datetime.utcnow() - timedelta(days=1)
        ).flatten()
        await message.channel.send(f"Found {len(bans)} in the last 24hrs")

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
