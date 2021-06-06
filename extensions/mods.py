from datetime import datetime, timedelta
from discord import AuditLogAction, Embed, Guild, Member, Message
from extensions.user_tracking.manager import UserTracker
import dippy


class ModeratorsExtension(dippy.Extension):
    client: dippy.Client
    user_tracking: UserTracker

    @dippy.Extension.listener("ready")
    async def on_ready(self):
        self.client.remove_command("help")

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
        members: list[Member] = [
            member for member in message.mentions if isinstance(member, Member)
        ] or [message.author]
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
