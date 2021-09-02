import nextcord
import json
from beginner.cog import Cog


class Python(Cog):
    def __init__(self, client):
        super().__init__(client)
        self.commands = self.load_data("python")

    @Cog.command()
    async def python(self, ctx, *, cmd):
        if not self.commands:
            await ctx.send("Nothing found in the database, try again later")
            return

        found = False
        if (
            "-missing" in cmd
        ):  # provide a list of python commands that are missing examples
            if len([r for r in ctx.author.roles if r.id == 644301991832453120]) > 0:
                found = True
                text = "The following items are missing example codes:\n\n"
                counter = 0
                page = 1
                for r in self.commands["responses"]:
                    if not r["code"]:
                        if len(text) < 1948:
                            counter += 1
                            if r["link"]:
                                text += f"[{r['alias']}]({r['link']}), "
                            else:
                                text += f"{r['alias']}, "
                        else:
                            text = text[:-2]
                            embedded = nextcord.Embed(description=text, color=0x306998)
                            if page == 1:
                                embedded.set_author(
                                    name="Missing", icon_url=self.server.icon_url
                                )
                            page += 1
                            text = ""
                            await ctx.send(embed=embedded)
                            counter = 0
                text = text[:-2]
                embedded = nextcord.Embed(description=text, color=0x306998)

        elif "-add code" in cmd:  # allow to add a new example code to a python command
            if len([r for r in ctx.author.roles if r.id == 644301991832453120]) > 0:
                items = cmd.split()
                item = items[2]
                rows = cmd.split("\n")
                code = "\n".join(rows[1:])
                found = True
                foundInner = False
                for r in self.commands["responses"]:
                    if r["alias"] == item or r["alias"] == item + "()":
                        foundInner = True
                        if len(r["code"]) < 2:
                            r["code"].append(code)
                            file = open("./cogs/python.json", "w")
                            file.write(json.dumps(self.commands))
                            file.close()
                            embedded = nextcord.Embed(
                                title="Success",
                                description=f"{r['alias']} {r['type']} successfully updated.",
                                color=0x22CC22,
                            )
                            embedded.set_author(
                                name="Success", icon_url=self.server.icon_url
                            )
                        else:
                            embedded = nextcord.Embed(
                                description=f"The *{r['alias']}* {r['type']} already has two examples, more cannot be added.",
                                color=0xCC2222,
                            )
                            embedded.set_author(
                                name="Error - limit reached",
                                icon_url=self.server.icon_url,
                            )
                        break

                if foundInner == False:
                    text = f"I'm sorry <@{ctx.author.id}>, it looks like you're trying to add an example to a python keyword or function that doesn't exist in my database."
                    embedded = nextcord.Embed(description=text, color=0xCC2222)
                    embedded.set_author(
                        name="Error - not found", icon_url=self.server.icon_url
                    )

        elif (
            "-edit text" in cmd
        ):  # allow to overwrite the existing description of a python command
            if len([r for r in ctx.author.roles if r.id == 644301991832453120]) > 0:
                items = cmd.split()
                item = items[2]
                description = " ".join(items[3:])
                found = True
                foundInner = False
                for r in self.commands["responses"]:
                    if r["alias"] == item or r["alias"] == item + "()":
                        foundInner = True
                        r["text"] = description
                        file = open("./cogs/python.json", "w")
                        file.write(json.dumps(self.commands))
                        file.close()
                        embedded = nextcord.Embed(
                            description=f"{r['alias']} successfully updated.",
                            color=0x22CC22,
                        )
                        embedded.set_author(
                            name="Success", icon_url=self.server.icon_url
                        )

                if foundInner == False:
                    text = f"I'm sorry <@{ctx.author.id}>, it looks like you're trying to edit the description of a python keyword or function that doesn't exist in my database."
                    embedded = nextcord.Embed(description=text, color=0xCC2222)
                    embedded.set_author(
                        name="Error - not found", icon_url=self.server.icon_url
                    )

        elif (
            "-edit code" in cmd
        ):  # allow to overwrite the example (or in case there are more than one examples, one example) code of a python command
            if len([r for r in ctx.author.roles if r.id == 644301991832453120]) > 0:
                items = cmd.split()
                item = items[2]
                try:
                    count = int(items[3])
                    rows = cmd.split("\n")
                    code = "\n".join(rows[1:])
                    found = True
                    foundInner = False
                    for r in self.commands["responses"]:
                        if r["alias"] == item or r["alias"] == item + "()":
                            foundInner = True
                            if len(r["code"]) >= count:
                                r["code"][count - 1] = code
                                file = open("./cogs/python.json", "w")
                                file.write(json.dumps(self.commands))
                                file.close()
                                embedded = nextcord.Embed(
                                    description=f"{r['alias']} successfully updated.",
                                    color=0x22CC22,
                                )
                                embedded.set_author(
                                    name="Success", icon_url=self.server.icon_url
                                )
                            else:
                                text = f"I'm sorry <@{ctx.author.id}>, it seems that the {r['alias']} python command has no example code #{count}."
                                embedded = nextcord.Embed(
                                    description=text, color=0xCC2222
                                )
                                embedded.set_author(
                                    name="Error - incorrect index",
                                    icon_url=self.server.icon_url,
                                )

                    if foundInner == False:
                        text = f"I'm sorry <@{ctx.author.id}>, it looks like you're trying to edit the description of a python keyword or function that doesn't exist in my database."
                        embedded = nextcord.Embed(description=text, color=0xCC2222)
                        embedded.set_author(
                            name="Error - not found", icon_url=self.server.icon_url
                        )

                except ValueError:
                    found = True
                    text = f"<@{ctx.author.id}>, the proper format for editing a code example is the following:\n!python -edit code <example_number>\n\```py\n# code here\n\```\n*<example_number> specifies which example should be overwritten (1 or 2).*"
                    embedded = nextcord.Embed(description=text, color=0xCC2222)
                    embedded.set_author(
                        name="Error - incorrect format", icon_url=self.server.icon_url
                    )

        else:
            for r in self.commands["responses"]:
                if r["alias"] == cmd or r["alias"] == cmd + "()":
                    found = True
                    embedded = nextcord.Embed(description=r["text"], color=0x306998)
                    embedded.set_author(
                        name=r["title"] + " " + r["type"], icon_url=self.server.icon_url
                    )
                    if len(r["code"]) == 0:
                        embedded.add_field(
                            name="Example",
                            value=f"Example code currently not available for this {r['type']}.",
                            inline=False,
                        )
                    elif len(r["code"]) == 1:
                        embedded.add_field(
                            name="Example", value=r["code"][0], inline=False
                        )
                    else:
                        for i in range(len(r["code"])):
                            embedded.add_field(
                                name=f"Example {i+1}", value=r["code"][i], inline=False
                            )

                    # <@{ctx.author.id}> gives a clickable link for the user
                    embedded.set_footer(
                        text=f"This information was requested by {ctx.author.name}.",
                        icon_url=self.server.icon_url,
                    )
                    break

        if found == False:
            text = f"I'm sorry <@{ctx.author.id}>, I don't know this Python keyword or function."
            embedded = nextcord.Embed(description=text, color=0xCC2222)
            embedded.set_author(name="Error - not found", icon_url=self.server.icon_url)

        await ctx.send(embed=embedded)


def setup(client):
    client.add_cog(Python(client))
