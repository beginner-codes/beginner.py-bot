from beginner.cog import Cog
from beginner.colors import *
from discord import Embed
from functools import cached_property
from typing import Set
import asyncio
import beginner.config
import discord
import os.path
import requests
import requests.auth


class SpamCog(Cog):
    file_types = {
        ".py": "python",
        ".c": "c",
        ".h": "c",
        ".cpp": "cpp",
        ".hpp": "cpp",
        ".cs": "csharp",
        ".sh": "shell",
        ".css": "css",
        ".csv": "csv",
        ".go": "go",
        ".html": "html",
        ".htm": "html",
        ".java": "java",
        ".js": "javascript",
        ".json": "json",
        ".jl": "julia",
        ".kt": "kotlin",
        ".sql": "sql",
        ".php": "php",
        ".rb": "ruby",
        ".rs": "rust",
        ".swift": "swift",
        ".xml": "xml",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".txt": "",
        ".dockerfile": "dockerfile",
    }

    @cached_property
    def admin_channels(self) -> Set:
        return set(channel.name for channel in self.get_category("Staff").text_channels)

    @Cog.listener()
    async def on_message(self, message):
        await asyncio.gather(
            self.attachment_filter(message), self.mention_filter(message)
        )

    async def mention_filter(self, message: discord.Message):
        if "@everyone" not in message.content and "@here" not in message.content:
            return

        if message.channel.permissions_for(message.author).manage_messages:
            return

        await asyncio.gather(
            message.channel.send(
                f"{message.author.mention} please don't mention everyone, your message has been deleted."
            ),
            message.delete(),
        )

    async def attachment_filter(self, message):
        """When a message is sent by normal users ensure it doesn't have any non-image attachments. Delete it and send
        a mod message if it does."""
        if message.author.bot:
            return

        if not message.attachments:
            return

        if os.environ.get("PRODUCTION_BOT", False):
            if message.channel.name.lower() in self.admin_channels:
                return

            if message.channel.permissions_for(message.author).manage_messages:
                return

        allowed, disallowed = self.categorize_attachments(message)

        if not allowed and not disallowed:
            return

        embed = Embed(
            title="File Attachments Not Allowed",
            description="For safety reasons we do not allow file and video attachments.",
            color=YELLOW,
        )

        if allowed:
            files = {}
            for attachment in allowed:
                files[attachment.filename] = (await attachment.read()).decode()

            gist = self.upload_files(files)
            embed.add_field(
                name="Uploaded the file to a Gist", value=f"[View file here]({gist})"
            )

        if disallowed:
            embed.add_field(
                name="Ignored these files",
                value="\n".join(
                    f"- {attachment.filename}" for attachment in disallowed
                ),
            )

        embed.set_thumbnail(
            url="https://cdn.discordapp.com/emojis/651959497698574338.png?v=1"
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

        try:
            await message.delete()
        except discord.errors.NotFound:
            pass

        await message.channel.send(message.author.mention, embed=embed)

    def categorize_attachments(self, message):
        allowed = []
        disallowed = []
        for attachment in message.attachments:
            _, extension = os.path.splitext(attachment.filename.lower())
            if (
                extension in self.file_types
                or attachment.filename.lower() == "dockerfile"
            ):
                allowed.append(attachment)
            elif extension not in {".gif", ".png", ".jpeg", ".jpg", ".bmp"}:
                disallowed.append(attachment)

        return allowed, disallowed

    def upload_files(self, files):
        data = {
            "files": {
                filename: {"content": content} for filename, content in files.items()
            },
            "public": "false",
        }
        resp = requests.post(
            "https://api.github.com/gists",
            json=data,
            auth=requests.auth.HTTPBasicAuth(*self.get_gist_auth()),
            headers={
                "accept": "application/vnd.github.v3+json",
            },
        )
        ret = resp.json()
        return ret.get("html_url")

    def get_gist_auth(self):
        user = beginner.config.get_setting(
            "gist_user", scope="bot", env_name="GIST_USER", default=""
        )
        token = beginner.config.get_setting(
            "gist_token", scope="bot", env_name="GIST_TOKEN", default=""
        )
        return user.strip(), token.strip()


def setup(client):
    client.add_cog(SpamCog(client))
