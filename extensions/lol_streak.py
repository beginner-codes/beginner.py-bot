from datetime import datetime
from typing import Optional
import dippy.labels
import discord


class LolStreakExtension(dippy.Extension):
    client: dippy.Client
    labels: dippy.labels.storage.StorageInterface

    def __init__(self):
        self.lol_counts = {}

    async def get_count(self, channel: discord.TextChannel) -> int:
        if channel.id not in self.lol_counts:
            self.lol_counts[channel.id] = await channel.get_label(
                "lol_count", default=0
            )

        return self.lol_counts[channel.id]

    async def set_count(self, channel: discord.TextChannel, count: int):
        self.lol_counts[channel.id] = count
        await channel.set_label("lol_count", count)

    @dippy.Extension.listener("message")
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        lol_count = await self.get_count(message.channel)
        if message.content.casefold().strip() == "lol":
            await self.set_count(message.channel, lol_count + 1)
            return

        if lol_count > 0:
            await message.channel.set_label("lol_count", 0)

        if lol_count > 1:
            await message.channel.send(
                f"{message.author.mention} has broken the {lol_count} LOL streak 😟",
                allowed_mentions=discord.AllowedMentions(users=False),
            )
