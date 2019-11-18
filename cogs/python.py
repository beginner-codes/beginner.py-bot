import discord
import json
from discord.ext import commands
from googlesearch import search

class Python(commands.Cog):

	def __init__(self, client):
		self.client = client
		with open("./cogs/python.json") as pyfile:
			python_data = json.load(pyfile)
		self.cmds = python_data
		pyfile.close()


	@commands.Cog.listener()	# event decorator inside a cog
	async def on_ready(self):
		print("Python cog ready.")


	@commands.command()			# command decorator inside a cog
	async def python(self, ctx, *, cmd):
		found = False
		if "-missing" in cmd:	# provide a list of python commands that are missing examples
			if len([r for r in ctx.author.roles if r.id == 644301991832453120]) > 0:
				found = True
				text = "The following items are missing example codes:\n\n"
				counter = 0
				page = 1
				for r in self.cmds["responses"]:
					if not r["code"]:
						if len(text) < 1948:
							counter += 1
							if r["link"]:
								text += f"[{r['alias']}]({r['link']}), "
							else:
								text += f"{r['alias']}, "
						else:
							text = text[:-2]
							embedded = discord.Embed(description=text, color=0x306998)
							if page == 1:
								embedded.set_author(name="Missing", icon_url="https://cdn.discordapp.com/icons/644299523686006834/e69f6d4231a6e58eed5884625c4b4931.png")
							page += 1
							text = ""
							await ctx.send(embed=embedded)
							counter = 0
				text = text[:-2]
				embedded = discord.Embed(description=text, color=0x306998)

		elif "-add code" in cmd:		# allow to add a new example code to a python command
			if len([r for r in ctx.author.roles if r.id == 644301991832453120]) > 0:
				items = cmd.split()
				item = items[2]
				rows = cmd.split("\n")
				code = "\n".join(rows[1:])
				found = True
				foundInner = False
				for r in self.cmds["responses"]:
					if r["alias"] == item or r["alias"] == item+"()":
						foundInner = True
						if len(r["code"]) < 2:
							r["code"].append(code)
							file = open("./cogs/python.json", "w")
							file.write(json.dumps(self.cmds))
							file.close()
							embedded = discord.Embed(title="Success", description=f"{r['alias']} {r['type']} successfully updated.", color=0x22CC22)
							embedded.set_author(name="Success", icon_url="https://cdn.discordapp.com/icons/644299523686006834/e69f6d4231a6e58eed5884625c4b4931.png")
						else:
							embedded = discord.Embed(description=f"The *{r['alias']}* {r['type']} already has two examples, more cannot be added.", color=0xCC2222)
							embedded.set_author(name="Error - limit reached", icon_url="https://cdn.discordapp.com/icons/644299523686006834/e69f6d4231a6e58eed5884625c4b4931.png")
						break

				if foundInner == False:
					text = f"I'm sorry <@{ctx.author.id}>, it looks like you're trying to add an example to a python keyword or function that doesn't exist in my database."
					embedded = discord.Embed(description=text, color=0xCC2222)
					embedded.set_author(name="Error - not found", icon_url="https://cdn.discordapp.com/icons/644299523686006834/e69f6d4231a6e58eed5884625c4b4931.png")

		elif "-edit text" in cmd:	# allow to overwrite the existing description of a python command
			if len([r for r in ctx.author.roles if r.id == 644301991832453120]) > 0:
				items = cmd.split()
				item = items[2]
				description = " ".join(items[3:])
				found = True
				foundInner = False
				for r in self.cmds["responses"]:
					if r["alias"] == item or r["alias"] == item+"()":
						foundInner = True
						r["text"] = description
						file = open("./cogs/python.json", "w")
						file.write(json.dumps(self.cmds))
						file.close()
						embedded = discord.Embed(description=f"{r['alias']} successfully updated.", color=0x22CC22)
						embedded.set_author(name="Success", icon_url="https://cdn.discordapp.com/icons/644299523686006834/e69f6d4231a6e58eed5884625c4b4931.png")

				if foundInner == False:
					text = f"I'm sorry <@{ctx.author.id}>, it looks like you're trying to edit the description of a python keyword or function that doesn't exist in my database."
					embedded = discord.Embed(description=text, color=0xCC2222)
					embedded.set_author(name="Error - not found", icon_url="https://cdn.discordapp.com/icons/644299523686006834/e69f6d4231a6e58eed5884625c4b4931.png")

		elif "-edit code" in cmd:	# allow to overwrite the example (or in case there are more than one examples, one example) code of a python command
			if len([r for r in ctx.author.roles if r.id == 644301991832453120]) > 0:
				items = cmd.split()
				item = items[2]
				try:
					count = int(items[3])
					rows = cmd.split("\n")
					code = "\n".join(rows[1:])
					found = True
					foundInner = False
					for r in self.cmds["responses"]:
						if r["alias"] == item or r["alias"] == item+"()":
							foundInner = True
							if len(r["code"]) >= count:
								r["code"][count - 1] = code
								file = open("./cogs/python.json", "w")
								file.write(json.dumps(self.cmds))
								file.close()
								embedded = discord.Embed(description=f"{r['alias']} successfully updated.", color=0x22CC22)
								embedded.set_author(name="Success", icon_url="https://cdn.discordapp.com/icons/644299523686006834/e69f6d4231a6e58eed5884625c4b4931.png")
							else:
								text = f"I'm sorry <@{ctx.author.id}>, it seems that the {r['alias']} python command has no example code #{count}."
								embedded = discord.Embed(description=text, color=0xCC2222)
								embedded.set_author(name="Error - incorrect index", icon_url="https://cdn.discordapp.com/icons/644299523686006834/e69f6d4231a6e58eed5884625c4b4931.png")
			
					if foundInner == False:
						text = f"I'm sorry <@{ctx.author.id}>, it looks like you're trying to edit the description of a python keyword or function that doesn't exist in my database."
						embedded = discord.Embed(description=text, color=0xCC2222)
						embedded.set_author(name="Error - not found", icon_url="https://cdn.discordapp.com/icons/644299523686006834/e69f6d4231a6e58eed5884625c4b4931.png")

				except ValueError:
					found = True
					text = f"<@{ctx.author.id}>, the proper format for editing a code example is the following:\n!python -edit code <example_number>\n\```py\n# code here\n\```\n*<example_number> specifies which example should be overwritten (1 or 2).*"
					embedded = discord.Embed(description=text, color=0xCC2222)
					embedded.set_author(name="Error - incorrect format", icon_url="https://cdn.discordapp.com/icons/644299523686006834/e69f6d4231a6e58eed5884625c4b4931.png")

		else:
			for r in self.cmds["responses"]:
				if r["alias"] == cmd or r["alias"] == cmd+"()":
					found = True
					embedded = discord.Embed(description=r["text"], color=0x306998)
					embedded.set_author(name=r["title"] + " " + r["type"], icon_url="https://cdn.discordapp.com/icons/644299523686006834/e69f6d4231a6e58eed5884625c4b4931.png")
					if len(r["code"]) == 0:
						embedded.add_field(name="Example", value=f"Example code currently not available for this {r['type']}.", inline=False)
					elif len(r["code"]) == 1:
						embedded.add_field(name="Example", value=r["code"][0], inline=False)
					else:
						for i in range(len(r["code"])):
							embedded.add_field(name=f"Example {i+1}", value=r["code"][i], inline=False)

					# <@{ctx.author.id}> gives a clickable link for the user
					embedded.set_footer(text=f"This information was requested by {ctx.author.name}.", icon_url="https://cdn.discordapp.com/icons/644299523686006834/e69f6d4231a6e58eed5884625c4b4931.png")
					break
		if found == False:
			text = f"I'm sorry <@{ctx.author.id}>, I don't know this Python keyword or function."
			embedded = discord.Embed(description=text, color=0xCC2222)
			embedded.set_author(name="Error - not found", icon_url="https://cdn.discordapp.com/icons/644299523686006834/e69f6d4231a6e58eed5884625c4b4931.png")

		await ctx.send(embed=embedded)
		


def setup(client):
	client.add_cog(Python(client))