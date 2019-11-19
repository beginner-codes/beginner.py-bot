import os
import discord
import random
from discord.ext import commands

client = commands.Bot(
	command_prefix="!",
	activity=discord.Activity(
		name="for '!help' to show you all commands",
		type=discord.ActivityType.watching
	)
)
client.remove_command('help')


@client.event
async def on_ready():
	print("Bot is ready.")


@client.command()
async def load(ctx, extension):
	if len([r for r in ctx.author.roles if r.id == 644301991832453120]) > 0:
		client.load_extension(f'cogs.{extension}')
		print(f"Loaded extension {extension}")
	else:
		print(f"Unauthorized attempt to use load() function from {ctx.author.name}.")
		await ctx.send(f"{ctx.author.name} you don't have permission to perform this action.")


@client.command()
async def unload(ctx, extension):
	if len([r for r in ctx.author.roles if r.id == 644301991832453120]) > 0:
		client.unload_extension(f'cogs.{extension}')
		print(f"Unloaded extension {extension}")
	else:
		print(f"Unauthorized attempt to use unload() function from {ctx.author.name}.")
		await ctx.send(f"{ctx.author.name} you don't have permission to perform this action.")


@client.command()
async def reload(ctx, extension):
	if len([r for r in ctx.author.roles if r.id == 644301991832453120]) > 0:
		client.unload_extension(f'cogs.{extension}')
		client.load_extension(f'cogs.{extension}')
		print(f"Reloaded extension {extension}")
	else:
		print(f"Unauthorized attempt to use reload() function from {ctx.author.name}.")
		await ctx.send(f"{ctx.author.name} you don't have permission to perform this action.")


for filename in os.listdir('./cogs'):
	if filename.endswith('.py'):
		client.load_extension(f'cogs.{filename[:-3]}')


client.run(os.environ["DISCORD_TOKEN"])
