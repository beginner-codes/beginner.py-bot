from beginner.cog import Cog
import discord
import discord.ext.commands
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
        if self.is_available_python_help_channel(message.channel):
            await self.rotate_available_channels(message)
        elif self.is_occupied_python_help_channel(message.channel):
            await self.rotate_occupied_channels(message)

    @Cog.command("free-channel", aliases=["free"])
    async def free_channel(self, ctx: discord.ext.commands.Context):
        await ctx.send(f"Please use this free channel which is currently not in use:\n{self.available_category.channels[0].mention}")

    async def rotate_available_channels(self, message: discord.Message):
        current_top_occupied = self.occupied_category.channels[0].position
        await message.channel.edit(category=self.occupied_category, position=current_top_occupied)

        next_channel = self.get_next_channel()
        available_insert = self.get_channel("web-dev").position
        await next_channel.edit(category=self.available_category, position=available_insert)

    async def rotate_occupied_channels(self, message: discord.Message):
        current_top_occupied = self.occupied_category.channels[0].position
        await message.channel.edit(category=self.occupied_category, position=current_top_occupied)

    def get_next_channel(self) -> discord.TextChannel:
        return self.occupied_category.text_channels[-1]

    def is_available_python_help_channel(self, channel: discord.TextChannel) -> bool:
        if channel.category_id != self.available_category.id:
            return False

        return channel.name.startswith("python-help-")

    def is_occupied_python_help_channel(self, channel: discord.TextChannel) -> bool:
        if channel.category_id != self.occupied_category.id:
            return False

        return channel.name.startswith("python-help-")


def setup(client):
    client.add_cog(HelpRotatorCog(client))
