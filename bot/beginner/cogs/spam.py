from beginner.cog import Cog
from beginner.scheduler import schedule
from beginner.tags import tag
from datetime import timedelta
from discord import Embed
from functools import cached_property
from typing import Set
import os.path


class SpamCog(Cog):
    def __init__(self, client):
        self.client = client

    @cached_property
    def admin_channels(self) -> Set:
        return set(channel.name for channel in self.get_category("staff").text_channels)

    @Cog.listener()
    async def on_ready(self):
        print("Spam Cog is ready")

    @Cog.listener()
    async def on_message(self, message):
        """ When a message is sent by normal users ensure it doesn't have any non-image attachments. Delete it and send
        a mod message if it does."""
        if message.author.bot:
            return

        if not message.attachments:
            return

        if message.channel.name.lower() in self.admin_channels:
            return

        if message.channel.permissions_for(message.author).manage_messages:
            return

        if self.has_disallowed_attachments(message):
            await message.channel.send(embed=self.build_embed(message))
            await message.delete()

    def build_embed(self, message):
        """ Construct the embed for the moderation message. """
        embed = Embed(
            description=f"{message.author.mention} you can only attach images.",
            color=0xFF0000,
        )
        embed.set_thumbnail(
            url="https://cdn.discordapp.com/emojis/651959497698574338.png?v=1"
        )
        embed.set_author(
            name="Message Deleted: File Attachments Not Allowed",
            icon_url=self.server.icon_url,
        )
        embed.add_field(
            name="Code Formatting",
            value=f"You can share your code using triple backticks like this:\n\\```\nYOUR CODE\n\\```",
            inline=False,
        )
        embed.add_field(
            name="Large Portions of Code",
            value=f"For longer scripts use [Hastebin](https://hastebin.com/) or "
            f"[GitHub Gists](https://gist.github.com/) and share the link here",
            inline=False,
        )
        return embed

    def has_disallowed_attachments(self, message):
        """ Check if a message has an attachment that is not an allowed image type. """
        for attachment in message.attachments:
            _, extension = os.path.splitext(attachment.filename)
            if extension[1:].lower() not in {"gif", "png", "jpeg", "jpg"}:
                return True
        return False


def setup(client):
    client.add_cog(SpamCog(client))
