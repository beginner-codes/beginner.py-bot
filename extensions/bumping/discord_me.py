import dippy
import asyncio
from datetime import datetime, timedelta


class DiscordMeBumpReminderExtension(dippy.Extension):
    client: dippy.Client
    log: dippy.logging.Logging

    def __init__(self):
        super().__init__()
        self.log.info("Discord.me bump reminder setting up")
        self.client.loop.create_task(self.schedule_next())

    async def send_reminder(self):
        channel = self.client.get_channel(813085810114297876)
        role = self.client.get_guild(644299523686006834).get_role(702177774315634788)
        await channel.send(
            f"{role.mention} time for the Discord.me bump https://discord.me/dashboard"
        )

    async def schedule_next(self):
        bump = self.get_next_bump()
        self.log.info(f"Scheduling next reminder in {bump} seconds")
        await asyncio.sleep(bump)
        self.log.info("Sending reminder")
        await self.send_reminder()
        self.client.loop.create_task(self.schedule_next())

    def get_next_bump(self) -> int:
        now = datetime.utcnow()
        bump = now.replace(minute=0, second=0, microsecond=0)
        bump += timedelta(hours=6 - bump.hour % 6 - 1, minutes=59, seconds=30)
        if bump < now + timedelta(minutes=5):
            bump += timedelta(hours=6)
        return int((bump - datetime.utcnow()).total_seconds())
