import discord
from beginner.cog import Cog


class Help(Cog):
    def __init__(self, client):
        self.client = client

    @Cog.listener()
    async def on_ready(self):
        print("Help cog ready.")

    @Cog.command()
    async def help(self, ctx, *, cmd=None):
        if not cmd:
            embedded = discord.Embed(
                title="beginner.py help",
                description="Commands:\ngoogle\npython\nrule",
                color=0xFFE873,
            )
            embedded.set_thumbnail(
                url="https://cdn.discordapp.com/icons/644299523686006834/e69f6d4231a6e58eed5884625c4b4931.png"
            )
            embedded.add_field(
                name="!python <keyword>",
                value="Returns a short information and example code of the Python keyword or function.",
                inline=False,
            )
            embedded.add_field(
                name="!google <search_phrase>",
                value="Returns 3 links matching the search criteria from Google.",
                inline=False,
            )
            embedded.add_field(
                name="!rule <alias>",
                value="Returns the rule matching the alias.",
                inline=False,
            )
            embedded.add_field(
                name="!rule <number>",
                value="Returns the rule matching the number.",
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
                    embedded = discord.Embed(
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
                        name="!rule -edit rule <alias> <content>",
                        value="Overwrites an existing rule's text with <content>.",
                        inline=False,
                    )
                    embedded.add_field(
                        name="!rule -edit alias <current_alias> <new_alias>",
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

                    embedded = discord.Embed(
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
                embedded = discord.Embed(
                    title="Error",
                    description="This channel has no access to the admin help option.",
                    color=0xCC2222,
                )
                await ctx.send(embed=embedded)

    @Cog.command()
    async def info(self, ctx):
        embedded = discord.Embed(
            description="I am the official beginner.py server bot. I'm here to make everyone's life easier on this server.\nType **!help** to see how you can get help from me.",
            color=0xFFE873,
        )
        await ctx.send(embed=embedded)


def setup(client):
    client.add_cog(Help(client))
