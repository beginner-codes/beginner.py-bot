from __future__ import annotations
from discord.ext.commands import Context
from beginner.cog import Cog
from beginner.config import get_setting
from beginner.colors import *
import discord


class ResourcesCog(Cog):
    @Cog.command(aliases=("r", "resource"))
    async def resources(self, ctx: Context, lang_name: str = "py"):
        lang_code = get_setting(lang_name.casefold(), scope="lang_aliases", default=lang_name.casefold())
        lang = get_setting(lang_code, scope="resources")

        if not lang:
            await ctx.send(f"Could not find any resources for `{lang_code}`")
            return

        await ctx.send(
            embed=discord.Embed(
                title=f"Helpful {lang['name']} Resources",
                description="Here are some resources you may find helpful.",
                color=YELLOW
            ).add_field(
                name="YouTube",
                value="\n".join(
                    f"[{name}]({url})" for name, url in lang["youtube"].items()
                ),
                inline=False,
            ).add_field(
                name="Books",
                value="\n".join(
                    f"[{name}]({url})" for name, url in lang["books"].items()
                ),
                inline=False,
            )
        )


def setup(client):
    client.add_cog(ResourcesCog(client))
