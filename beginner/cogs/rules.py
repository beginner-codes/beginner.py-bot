import discord
from beginner.cog import AdvancedCommand, Cog
from typing import AnyStr, Dict


class Rules(Cog):
    def __init__(self, client):
        self.client = client
        self.rules = self.load_data("rules", {"responses": [], "callfunc": "rule"})

    @Cog.listener()
    async def on_ready(self):
        print("Rules cog ready.")

    @Cog.command()
    async def rule(self, ctx, *args):
        if not self.rules:
            await ctx.send("No rules found in the database, try again later")
            if len([r for r in ctx.author.roles if r.id == 644301991832453120]) > 0:
                # TODO: This is debug code for use on the cluster. Will be removed later.
                import os

                await ctx.send(f">>> {os.getcwd()}\n{os.listdir(os.getcwd())}")
        else:
            command = AdvancedCommand(self.show_rule)
            command.add("-add", self.add_rule)
            command.add("-edit", self.edit_rule)
            command.add("-edit-alias", self.edit_rule_alias)
            await command.run(ctx, *args)

    async def add_rule(self, ctx, alias: AnyStr, *rule):
        if len([r for r in ctx.author.roles if r.id == 644301991832453120]) > 0:
            error_message = ""
            error_sub = ""
            if alias.isnumeric():
                error_message = f"*{alias}* is an invalid rule alias."
                error_sub = "invalid alias"
            elif self.find_rule(alias):
                error_message = f"A rule with the alias *{alias}* already exists."
                error_sub = "alias exists"
            else:
                text = " ".join(rule)
                self.rules["responses"].append({"alias": alias, "text": text})
                self.update_data("rules", self.rules)

                embedded = discord.Embed(
                    description=f"Rules successfully updated with new rule:\n\n**Rule {len(self.rules['responses'])}** - *{alias}*\n{text}.",
                    color=0x22CC22,
                )
                embedded.set_author(
                    name="Success",
                    icon_url="https://cdn.discordapp.com/icons/644299523686006834/e69f6d4231a6e58eed5884625c4b4931.png",
                )
                await ctx.send(embed=embedded)

            if error_message:
                embedded = discord.Embed(
                    description=error_message,
                    color=0xCC2222,
                )
                embedded.set_author(
                    name=f"Error - {error_sub}",
                    icon_url="https://cdn.discordapp.com/icons/644299523686006834/e69f6d4231a6e58eed5884625c4b4931.png",
                )
                await ctx.send(embed=embedded)

    async def edit_rule(self, ctx, identifier: AnyStr, *message):
        if len([r for r in ctx.author.roles if r.id == 644301991832453120]) > 0:
            rule = self.find_rule(identifier)
            if rule:
                rule[1]["text"] = " ".join(message)
                self.update_data("rules", self.rules)

                embedded = discord.Embed(
                    description=f"Rule *{rule[1]['alias']}* successfully updated to the following:\n{rule[1]['text']}.",
                    color=0x22CC22,
                )
                embedded.set_author(
                    name="Success",
                    icon_url="https://cdn.discordapp.com/icons/644299523686006834/e69f6d4231a6e58eed5884625c4b4931.png",
                )
                await ctx.send(embed=embedded)
            else:
                embedded = discord.Embed(
                    description=f"A rule with the alias *{identifier}* doesn't exist.",
                    color=0xCC2222,
                )
                embedded.set_author(
                    name="Error - missing alias",
                    icon_url="https://cdn.discordapp.com/icons/644299523686006834/e69f6d4231a6e58eed5884625c4b4931.png",
                )
                await ctx.send(embed=embedded)

    async def edit_rule_alias(self, ctx, identifier: AnyStr, alias: AnyStr, *_):
        if len([r for r in ctx.author.roles if r.id == 644301991832453120]) > 0:
            rule = self.find_rule(identifier)
            if rule:
                rule[1]["alias"] = alias
                self.update_data("rules", self.rules)

                embedded = discord.Embed(
                    description=f"Rule *{rule[0]}* alias changed to {alias}.",
                    color=0x22CC22,
                )
                embedded.set_author(
                    name="Success",
                    icon_url="https://cdn.discordapp.com/icons/644299523686006834/e69f6d4231a6e58eed5884625c4b4931.png",
                )
                await ctx.send(embed=embedded)
            else:
                embedded = discord.Embed(
                    description=f"No rule found for *{identifier}*.",
                    color=0xCC2222,
                )
                embedded.set_author(
                    name="Error - invalid rule",
                    icon_url="https://cdn.discordapp.com/icons/644299523686006834/e69f6d4231a6e58eed5884625c4b4931.png",
                )
                await ctx.send(embed=embedded)

    async def show_rule(self, ctx, identifier: AnyStr, *_):
        rule = self.find_rule(identifier)
        if rule:
            embedded = discord.Embed(
                description=rule[1]["text"],
                color=0x306998,
            )
            embedded.set_author(
                name=f"Rule {rule[0]} - {rule[1]['alias']}",
                icon_url="https://cdn.discordapp.com/icons/644299523686006834/e69f6d4231a6e58eed5884625c4b4931.png",
            )
            await ctx.send(embed=embedded)
        else:
            message = f"Invalid rule number. The valid rule numbers are between 1 and 13."
            if not identifier.isnumeric() and not identifier[1:].isnumeric():
                aliases = ', '.join(
                    sorted(
                        [
                            _rule["alias"]
                            for _rule in self.rules["responses"]
                        ]
                    )
                )
                message = f"*{identifier}* is not a valid rule. The valid rules are:\n{aliases}"
            embedded = discord.Embed(description=message, color=0xCC2222)
            embedded.set_author(
                name="Error - incorrect alias",
                icon_url="https://cdn.discordapp.com/icons/644299523686006834/e69f6d4231a6e58eed5884625c4b4931.png",
            )
            await ctx.send(embed=embedded)

    @Cog.command()
    async def aliases(self, ctx):
        als = sorted([rule["alias"] for rule in self.rules["responses"]])
        await ctx.send(f">>> The available rule aliases are:\n{', '.join(als)}")

    def find_rule(self, identifier: AnyStr) -> Dict:
        rule = None
        rule_index = -1
        if identifier.isnumeric():
            rule_index = int(identifier)
            if 0 < rule_index <= len(self.rules["responses"]):
                rule = self.rules["responses"][rule_index - 1]
        else:
            rules = self.rules["responses"]
            for rule_index, _rule in zip(range(1, len(rules) + 1), rules):
                if _rule["alias"] == identifier.lower():
                    rule = _rule
                    break
        return (rule_index, rule) if rule else None


def setup(client):
    client.add_cog(Rules(client))
