import discord
import json
from beginner.cog import Cog


class Rules(Cog):
    def __init__(self, client):
        self.client = client
        self.rules = self.load_data("rules")

    @Cog.listener()
    async def on_ready(self):
        print("Rules cog ready.")

    @Cog.command()
    async def rule(self, ctx, *, cmd):
        if not self.rules:
            await ctx.send("No rules found in the database, try again later")
            if len([r for r in ctx.author.roles if r.id == 644301991832453120]) > 0:
                # TODO: This is debug code for use on the cluster. Will be removed later.
                import os

                await ctx.send(f">>> {os.getcwd()}\n{os.listdir(os.getcwd())}")
            return

        found = False
        if "-add rule" in cmd:  # allow to add a new rule
            items = cmd.split()
            alias = items[2]
            rule = " ".join(items[3:])
            if len([r for r in ctx.author.roles if r.id == 644301991832453120]) > 0:
                found = True
                foundInner = False
                for r in self.rules["responses"]:
                    if r["alias"] == alias:
                        foundInner = True
                        embedded = discord.Embed(
                            description=f"A rule with the alias *{alias}* already exists.",
                            color=0xCC2222,
                        )
                        embedded.set_author(
                            name="Error - existing alias",
                            icon_url="https://cdn.discordapp.com/icons/644299523686006834/e69f6d4231a6e58eed5884625c4b4931.png",
                        )
                        break
                if foundInner == False:
                    self.rules["responses"].append({"alias": alias, "text": rule})
                    file = open("./cogs/rules.json", "w")
                    file.write(json.dumps(self.rules))
                    file.close()
                    embedded = discord.Embed(
                        description=f"Rules successfully updated with new rule:\n\n**Rule {len(self.rules['responses'])}** - *{alias}*\n{rule}.",
                        color=0x22CC22,
                    )
                    embedded.set_author(
                        name="Success",
                        icon_url="https://cdn.discordapp.com/icons/644299523686006834/e69f6d4231a6e58eed5884625c4b4931.png",
                    )

        elif "-edit rule" in cmd:  # allow to edit an existing rule
            items = cmd.split()
            alias = items[2]
            rule = " ".join(items[3:])
            if len([r for r in ctx.author.roles if r.id == 644301991832453120]) > 0:
                found = True
                foundInner = False
                for r in self.rules["responses"]:
                    if r["alias"] == alias:
                        foundInner = True
                        r["text"] == rule
                        file = open("./cogs/rules.json", "w")
                        file.write(json.dumps(self.rules))
                        file.close()
                        embedded = discord.Embed(
                            description=f"Rule *{alias}* successfully updated to the following:\n{rule}.",
                            color=0x22CC22,
                        )
                        embedded.set_author(
                            name="Success",
                            icon_url="https://cdn.discordapp.com/icons/644299523686006834/e69f6d4231a6e58eed5884625c4b4931.png",
                        )
                        break
                if foundInner == False:
                    embedded = discord.Embed(
                        description=f"A rule with the alias *{r['alias']}* doesn't exist.",
                        color=0xCC2222,
                    )
                    embedded.set_author(
                        name="Error - missing alias",
                        icon_url="https://cdn.discordapp.com/icons/644299523686006834/e69f6d4231a6e58eed5884625c4b4931.png",
                    )

        elif "-edit alias" in cmd:  # allow to edit an existing rule
            items = cmd.split()
            alias1 = items[2]
            alias2 = items[3]
            if len([r for r in ctx.author.roles if r.id == 644301991832453120]) > 0:
                found = True
                foundInner = False
                for r in self.rules["responses"]:
                    if r["alias"] == alias1:
                        foundInner = True
                        r["alias"] == alias2
                        file = open("./cogs/rules.json", "w")
                        file.write(json.dumps(self.rules))
                        file.close()
                        embedded = discord.Embed(
                            description=f"Rule alias *{alias1}* successfully updated to *{alias2}*.",
                            color=0x22CC22,
                        )
                        embedded.set_author(
                            name="Success",
                            icon_url="https://cdn.discordapp.com/icons/644299523686006834/e69f6d4231a6e58eed5884625c4b4931.png",
                        )
                        break
                if foundInner == False:
                    embedded = discord.Embed(
                        description=f"A rule with the alias *{r['alias']}* doesn't exist.",
                        color=0xCC2222,
                    )
                    embedded.set_author(
                        name="Error - missing alias",
                        icon_url="https://cdn.discordapp.com/icons/644299523686006834/e69f6d4231a6e58eed5884625c4b4931.png",
                    )

        else:
            try:
                r = int(cmd)
                if r < 1 or r > len(self.rules["responses"]):
                    embedded = discord.Embed(
                        description=f"There is no rule #{r}. The valid rule numbers are between 1 and {len(self.rules['responses'])}.",
                        color=0xCC2222,
                    )
                    embedded.set_author(
                        name="Error - incorrect number",
                        icon_url="https://cdn.discordapp.com/icons/644299523686006834/e69f6d4231a6e58eed5884625c4b4931.png",
                    )
                else:
                    embedded = discord.Embed(
                        description=self.rules["responses"][r - 1]["text"],
                        color=0x306998,
                    )
                    embedded.set_author(
                        name=f"Rule {cmd} - {self.rules['responses'][r - 1]['alias']}",
                        icon_url="https://cdn.discordapp.com/icons/644299523686006834/e69f6d4231a6e58eed5884625c4b4931.png",
                    )
            except ValueError:
                found = False
                for r in self.rules["responses"]:
                    if r["alias"] == cmd:
                        found = True
                        embedded = discord.Embed(description=r["text"], color=0x306998)
                        embedded.set_author(
                            name=f"Rule {self.rules['responses'].index(r)} - {r['alias']}",
                            icon_url="https://cdn.discordapp.com/icons/644299523686006834/e69f6d4231a6e58eed5884625c4b4931.png",
                        )
                if found == False:
                    text = "*" + cmd + "* is not a valid rule alias. The aliases are:\n"
                    als = []
                    for r in self.rules["responses"]:
                        als.append(r["alias"])
                    als = sorted(als)
                    for r in als:
                        text += r + ", "
                    text = text[:-2]
                    embedded = discord.Embed(description=text, color=0xCC2222)
                    embedded.set_author(
                        name="Error - incorrect alias",
                        icon_url="https://cdn.discordapp.com/icons/644299523686006834/e69f6d4231a6e58eed5884625c4b4931.png",
                    )
        await ctx.send(embed=embedded)

    @Cog.command()
    async def aliases(self, ctx):
        als = sorted([rule["alias"] for rule in self.rules["responses"]])
        await ctx.send(f">>> The available rule aliases are:\n{', '.join(als)}")


def setup(client):
    client.add_cog(Rules(client))
