from __future__ import annotations
from discord.ext.commands import Context
from beginner.cog import Cog
from beginner.config import get_setting
from beginner.colors import *
import discord


class ResourcesCog(Cog):
    @Cog.command(aliases=("r", "resource"))
    async def resources(self, ctx: Context, *, lang_name: str = "py"):
        lang_code = get_setting(
            lang_name.casefold(), scope="lang_aliases", default=lang_name.casefold()
        )
        lang = get_setting(lang_code, scope="resources")

        if not lang:
            await ctx.send(f"Could not find any resources for `{lang_code}`")
            return

        embed = discord.Embed(
            title=f"Helpful {lang['name']} Resources",
            description="Here are some resources you may find helpful.",
            color=YELLOW,
        )

        for title, resources in (
            section for section in lang.items() if section[0] != "name"
        ):
            embed.add_field(
                name=title,
                value="\n".join(f"[{name}]({url})" for name, url in resources.items()),
                inline=False,
            )

        await ctx.send(embed=embed)

    @Cog.command(alias=["project-ideas"])
    async def project(self, ctx):
        project_embed = discord.Embed(
            title="Project Ideas",
            description=(
                f"{ctx.author.mention} Here's our official list of "
                f"[project ideas!](https://github.com/beginnerpy-com/project-ideas)"
            ),
            color=BLUE,
            url="https://github.com/beginnerpy-com/project-ideas",
        )
        await ctx.send(embed=project_embed)


def setup(client):
    client.add_cog(ResourcesCog(client))
