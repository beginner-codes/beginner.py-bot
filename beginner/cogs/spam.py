import re

from beginner.cog import Cog
from beginner.colors import *
from nextcord import Embed, TextChannel, Message
from nextcord.ext import commands
from functools import cached_property
from typing import Optional, Set
import asyncio
import beginner.config
import nextcord
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
        ".dat": "dat",
    }

    embed_extensions = {
        ".gif",
        ".png",
        ".jpeg",
        ".jpg",
        ".bmp",
        ".webp",
        ".mp4",
        ".mov",
        ".webm",
        ".mp3",
    }

    @cached_property
    def admin_channels(self) -> Set:
        return set(channel.name for channel in self.get_category("Staff").text_channels)

    @Cog.command(name="delete-gist")
    @commands.has_any_role(720655282115706892, 644390354157568014)
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
        await self.newline_filter(message)

    async def newline_filter(self, message: nextcord.Message):
        count = message.content.count("\n")
        if count < 10:
            return

        if count / len(message.content) < 0.25:
            return

        await asyncio.gather(
            message.channel.send(
                f"{message.author.mention} your message has been deleted for having an excessive number of lines.",
                delete_after=60,
            ),
            message.delete(),
        )

    def escape_markdown(self, string):
        return re.sub(r"([_*|])", r"\\\g<1>", string)

    def escape_github_file_name(self, string):
        return re.sub(r"[^a-z0-9_]+", "-", string)

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
            elif extension not in self.embed_extensions:
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
