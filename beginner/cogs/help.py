import nextcord
from beginner.cog import Cog


class Help(Cog):
    @Cog.command(aliases=["commands"])
    async def help(self, ctx, *, cmd=None):
        if not cmd:
            embedded = nextcord.Embed(
                title="Beginner.py Commands",
                description=(
                    "**Commands:**\n- exec/eval\n- free\n- google\n- kudos\n- pip\n- resources\n- tip"
                ),
                color=0xFFE873,
            )
            embedded.set_thumbnail(url=self.server.icon_url)
            embedded.add_field(
                name="!exec <code block>",
                value=(
                    "Runs a block of python code. The code must be inside of a python markdown code block.\n\n"
                    '!exec \\```py\nfor i in range(5):\n    print("Hello world!!!")\n\\```'
                ),
                inline=False,
            )
            embedded.add_field(
                name="!eval <python statement>",
                value='Runs the python statement.\n```\n!eval print("Hello world!!!")\n```',
                inline=False,
            )
            embedded.add_field(
                name="!free",
                value="Gets a currently free Python help channel.\n```\n!free\n```",
                inline=False,
            )
            embedded.add_field(
                name="!google <search terms>",
                value="Gets retrieves the top 5 results from Google for the search term.\n```\n!google foobar\n```",
                inline=False,
            )
            embedded.add_field(
                name="!kudos [leaderboard|help]",
                value=(
                    "Gets your kudos score\n```\n!kudos\n```\n"
                    "Gets the kudos leaderboard\n```\n!kudos leaderboard\n```\n"
                    "Explains how kudos works\n```\n!kudos help\n```"
                ),
                inline=False,
            )
            embedded.add_field(
                name="!pip <package name>",
                value="Looks up a python package on the Python Package Index\n```\n!pip requests\n```",
                inline=False,
            )
            embedded.add_field(
                name="!resources <topic>",
                value="Retrieves our recommended resources for a given topic.\n```\n!resources python\n```",
                inline=False,
            )
            embedded.add_field(
                name="!tip <topic>",
                value=(
                    "Retrieves a tip message.\n```\n!tip cli\n```"
                    "Lists all available tips.\n```\n!tip\n```"
                ),
                inline=False,
            )
            await ctx.send(embed=embedded)
        else:
            if ctx.channel.id in [
                644338578695913504,
                644391251109740554,
                644309581476003860,
            ]:
                if cmd == "-admin":
                    embedded = nextcord.Embed(
                        title="Admin help",
                        description="Commands used to modify the content used by this bot are listed below.",
                        color=0xFFE873,
                    )
                    embedded.set_thumbnail(
                        url="https://cdn.discordapp.com/icons/644299523686006834/e69f6d4231a6e58eed5884625c4b4931.png"
                    )
                    embedded.add_field(
                        name="!rule -add <alias> <content>",
                        value="Creates a new rule with the provided name <alias> and text <content>.",
                        inline=False,
                    )
                    embedded.add_field(
                        name="!rule -edit <alias> <content>",
                        value="Overwrites an existing rule's text with <content>.",
                        inline=False,
                    )
                    embedded.add_field(
                        name="!rule -edit-alias <current_alias> <new_alias>",
                        value="Overwrites an existing rule's current alias with a new alias.",
                        inline=False,
                    )
                    embedded.add_field(
                        name="!python -missing",
                        value="Returns a list of Python keywords that currently have no example code yet.",
                        inline=False,
                    )
                    embedded.add_field(
                        name="!python -add <field> <keyword> <content>",
                        value="Adds a new value to the field of the keyword.",
                        inline=False,
                    )
                    embedded.add_field(
                        name="!python -edit <field> <keyword> <index> <content>",
                        value="Updates the value of an existing field of the keyword. When editing example codes, the index number of the code block (1 or 2) must be provided as well.",
                        inline=False,
                    )
                    await ctx.send(embed=embedded)

                    embedded = nextcord.Embed(
                        title="Admin help explanation",
                        description="Commands for modifying this bot's content use the following attributes in their description.",
                        color=0xFFE873,
                    )
                    embedded.set_thumbnail(
                        url="https://cdn.discordapp.com/icons/644299523686006834/e69f6d4231a6e58eed5884625c4b4931.png"
                    )
                    embedded.add_field(
                        name="<field>",
                        value="The field to be edited: *text* to edit the description, *code* to edit the example code blocks.",
                        inline=False,
                    )
                    embedded.add_field(
                        name="<keyword>",
                        value="A Python keyword or function name.",
                        inline=False,
                    )
                    embedded.add_field(
                        name="<index>",
                        value="Only required for editing example code. Represents the number of the code block to be edited. It can be 1 or 2.",
                        inline=False,
                    )
                    embedded.add_field(
                        name="<content>",
                        value="Any string of text. Quotation marks should **not** be added to surround the text.\nExample code blocks can be written just like regularly on Discord, in a new line (Shift+Enter), starting with \```py.",
                        inline=False,
                    )
                    await ctx.send(embed=embedded)
            else:
                embedded = nextcord.Embed(
                    title="Error",
                    description="This channel has no access to the admin help option.",
                    color=0xCC2222,
                )
                await ctx.send(embed=embedded)

    @Cog.command()
    async def info(self, ctx):
        embedded = nextcord.Embed(
            description="I am the official beginner.py server bot. I'm here to make everyone's life easier on this server.\nType **!help** to see how you can get help from me.",
            color=0xFFE873,
        )
        await ctx.send(embed=embedded)


def setup(client):
    client.add_cog(Help(client))
