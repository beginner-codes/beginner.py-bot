from __future__ import annotations
from nextcord.ext.commands import Context
from beginner.cog import Cog
from beginner.config import get_setting, get_scope
from beginner.colors import *
import nextcord


class ResourcesCog(Cog):
    @Cog.command(aliases=("r", "resource"))
    async def resources(self, ctx: Context, *, search_tag: str = "__all__"):
        if search_tag == "__all__":
            embed = nextcord.Embed(
                title="Helpful Resources",
                description=(
                    f"{ctx.author.mention} here are all the topics we currently have resources for. "
                    f"Use the `{ctx.prefix}resources <topic>` command to get resources for a specific topic."
                ),
                color=YELLOW,
            )

            embed.add_field(
                name="Topics",
                value="\n".join(
                    f"{topic['name']}: `!r {tag}`"
                    for tag, topic in sorted(
                        get_scope("resources"), key=lambda i: i[1]["name"]
                    )
                ),
                inline=False,
            )

            await ctx.send(embed=embed)
            return

        topic_tag = get_setting(
            search_tag.casefold(), scope="lang_aliases", default=search_tag.casefold()
        )
        topic = get_setting(topic_tag, scope="resources")

        if not topic:
            await ctx.send(f"Could not find any resources for `{topic_tag}`")
            return

        embed = nextcord.Embed(
            title=f"Helpful {topic['name']} Resources",
            description="Here are some resources you may find helpful.",
            color=YELLOW,
        )

        for title, resources in (
            section for section in topic.items() if section[0] != "name"
        ):
            embed.add_field(
                name=title,
                value="\n".join(
                    f"[{name}]({setting})"
                    if isinstance(setting, str)
                    else f"> **{name}**\n> {setting['message']}"
                    for name, setting in resources.items()
                ),
                inline=False,
            )

        await ctx.send(embed=embed)

    @Cog.command(aliases=["project-ideas", "ideas"])
    async def project(self, ctx):
        project_embed = nextcord.Embed(
            title="Project Ideas",
            description=(
                f"{ctx.author.mention} Here's our official list of "
                f"[project ideas!](https://github.com/beginnerpy-com/project-ideas)"
            ),
            color=BLUE,
            url="https://github.com/beginnerpy-com/project-ideas",
        ).set_thumbnail(
            url="https://emojipedia-us.s3.dualstack.us-west-1.amazonaws.com/thumbs/120/twitter/282/brain_1f9e0.png"
        )
        await ctx.send(embed=project_embed)


def setup(client):
    client.add_cog(ResourcesCog(client))
