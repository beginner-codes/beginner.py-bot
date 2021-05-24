from datetime import datetime, timedelta
from discord import AuditLogAction, Guild, Message
import dippy


class ModeratorsExtension(dippy.Extension):
    client: dippy.Client

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
