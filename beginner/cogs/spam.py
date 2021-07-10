import re

from beginner.cog import Cog
from beginner.colors import *
from discord import Embed
from discord.ext import commands
from functools import cached_property
from typing import Optional, Set
import asyncio
import beginner.config
import discord
import os.path
import aiohttp
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

    @Cog.command(name="delete-gist")
    @commands.has_guild_permissions(manage_messages=True)
    async def delete_gist(self, ctx, gist_url: str):
        deleted = await self.delete_gist_by_url(gist_url)
        message = "The Gist has been deleted"
        if not deleted:
            message = (
                "There was an issue deleting the gist, make sure it's a valid gist URL"
            )
        await ctx.send(message, delete_after=15)

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

        user_message = (
            "\n".join(f"> {section}" for section in message.content.split("\n"))
            if message.content.strip()
            else ""
        )
        embed = Embed(
            title="File Attachments Not Allowed",
            description=f"For safety reasons we do not allow file and video attachments.",
            color=YELLOW,
        )

        if allowed:
            embed.title = f"{message.author.display_name} Uploaded Some Code"
            embed.description = user_message
            files = {}
            name = None
            for attachment in allowed:
                content = (await attachment.read()).decode()
                if len(content) < 1000:
                    file_type = os.path.splitext(attachment.filename)[1].casefold()
                    embed.add_field(
                        name=f"Attachment: {attachment.filename}",
                        value=f"```{self.file_types.get(file_type, '')}\n{content}\n```",
                    )
                else:
                    if not name:
                        name = attachment.filename
                    files[attachment.filename] = content

            if files:
                gist = self.upload_files(files)
                embed.add_field(
                    name="Uploaded the file to a Gist",
                    value=f"[{name}]({gist})",
                )

            embed.set_thumbnail(
                url="https://cdn.discordapp.com/emojis/711749954837807135.png?v=1"
            )

            embed.set_footer(
                text="For safety reasons we do not allow file attachments."
            )

        else:
            embed.set_thumbnail(
                url="https://cdn.discordapp.com/emojis/651959497698574338.png?v=1"
            )
            embed.add_field(
                name=f"{message.author.display_name} Said", value=user_message
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

        if disallowed:
            embed.add_field(
                name="Ignored these files",
                value="\n".join(f"- {attachment.filename}" for attachment in disallowed)
                or "*NO FILES*",
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
            elif extension not in {".gif", ".png", ".jpeg", ".jpg", ".bmp", ".webp"}:
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

    async def delete_gist_by_url(self, gist_url: str) -> bool:
        gist_id = self.get_gist_id_from_url(gist_url)
        if not gist_id:
            return False

        return await self.delete_gist_by_id(gist_id)

    async def delete_gist_by_id(self, gist_id: str) -> bool:
        async with aiohttp.ClientSession() as session:
            try:
                await session.delete(
                    f"https://api.github.com/gists/{gist_id}",
                    auth=aiohttp.BasicAuth(*self.get_gist_auth()),
                    raise_for_status=True,
                )
            except aiohttp.ClientResponseError:
                return False
            else:
                return True

    def get_gist_id_from_url(self, gist_url: str) -> Optional[str]:
        try:
            gist_id, *_ = re.match(
                r"https?://gist.github.com/.+?/([a-z0-9]+)", gist_url, re.IGNORECASE
            ).groups()
        except AttributeError:
            return None
        else:
            return gist_id

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
