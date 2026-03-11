import nextcord
from beginner.cog import Cog


class Help(Cog):
    @Cog.command(aliases=["commands"])
    async def help(self, ctx, *, cmd=None):
        if not cmd:
            embedded = nextcord.Embed(
                title="Beginner.py Commands",
                description=(
                    "**Commands:**\n- resources\n- rules\n- help\n- info"
                ),
                color=0xFFE873,
            )
            embedded.set_thumbnail(url=self.server.icon.url)
            embedded.add_field(
                name="!resources <topic>",
                value="Retrieves our recommended resources for a given topic.\n```\n!resources python\n```",
                inline=False,
            )
            embedded.add_field(
                name="!rules <rule>",
                value="Displays the server rules.\n```\n!rules\n```",
                inline=False,
            )
            embedded.add_field(
                name="!info",
                value="Displays information about the bot.\n```\n!info\n```",
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
