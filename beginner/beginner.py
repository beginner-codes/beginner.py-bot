import os
import discord
from discord.ext import commands
from functools import lru_cache


@lru_cache()
def get_client() -> commands.Bot:
	client = commands.Bot(
		command_prefix="!",
		activity=discord.Activity(
			name="for '!help' to show you all commands",
			type=discord.ActivityType.watching
		)
	)
	client.remove_command('help')
	return client


@lru_cache()
def get_token():
	if "DISCORD_TOKEN" in os.environ:
		return os.environ.get("DISCORD_TOKEN")
	with open("bot.token", "r") as token_file:
		return token_file.readline().strip()


client = get_client()


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


def load_cogs():
	client.load_extension('beginner.cogs.google')
	client.load_extension('beginner.cogs.help')
	client.load_extension('beginner.cogs.python')
	client.load_extension('beginner.cogs.rules')
