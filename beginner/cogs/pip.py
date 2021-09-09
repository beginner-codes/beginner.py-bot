from __future__ import annotations
from beginner.colors import *
from beginner.cog import Cog
from nextcord.ext.commands import Context
from typing import Any, Optional
import nextcord
import requests
import xmltodict


class PipCog(Cog):
    @Cog.command()
    async def pip(self, ctx: Context, package_name: str):
        package = self.get_package(package_name)

        title = f"PyPI: {package_name} - NOT FOUND"
        description = "No packages by that name found."
        color = RED

        if package:
            latest = version = package["rss"]["channel"]["item"][0]
            author = latest.get("author", "*NO AUTHOR SET*")
            description = latest.get("description", "*NO DESCRIPTION*")
            link = latest["link"]
            released = latest["pubDate"]
            version = latest.get("title", "*NO VERSION SET*")

            title = f"PyPI: {package_name} {version}"
            description = (
                f"{description}\n\n{author} - {released}\n\n[Find on PyPI]({link})"
            )
            color = BLUE

        await ctx.send(
            embed=nextcord.Embed(
                title=title,
                description=description,
                color=color,
            ).set_thumbnail(
                url="https://pbs.twimg.com/profile_images/909757546063323137/-RIWgodF_400x400.jpg"
            )
        )

    def get_package(self, package_name: str) -> Optional[dict[str, Any]]:
        clean_name = package_name.lower().strip()
        response = requests.get(
            f"https://pypi.org/rss/project/{clean_name}/releases.xml"
        )
        if response.status_code != 200:
            return None

        return xmltodict.parse(response.content)


def setup(client):
    client.add_cog(PipCog(client))
