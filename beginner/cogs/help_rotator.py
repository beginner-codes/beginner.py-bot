from beginner.cog import Cog
import discord
import asyncio


class HelpRotatorCog(Cog):
    @property
    def available_category(self) -> discord.CategoryChannel:
        return self.get_category("Help: Available")

    @property
    def occupied_category(self) -> discord.CategoryChannel:
        return self.get_category("Help: Occupied")

    @Cog.listener()
    async def on_message(self, message: discord.Message):
        if not self.is_available_python_help_channel(message.channel):
            return

        current_top_available = self.available_category.channels[1].position + 1
        current_top_occupied = self.occupied_category.channels[0].position
        next_channel = self.get_next_channel()
        await message.channel.edit(category=self.occupied_category, position=current_top_occupied)
        await next_channel.edit(category=self.available_category, position=current_top_available)

    @Cog.command("free-channel", aliases=["free"])
    async def free_channel(self, ctx):
        await ctx.send(f"{self.available_category.channels[0].mention}")

    def get_next_channel(self) -> discord.TextChannel:
        return self.occupied_category.text_channels[-1]

    def is_available_python_help_channel(self, channel: discord.TextChannel) -> bool:
        if channel.category_id != self.available_category.id:
            return False

        return channel.name.startswith("python-help-")


def setup(client):
    client.add_cog(HelpRotatorCog(client))
