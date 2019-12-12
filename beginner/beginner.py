from asyncio import sleep
from beginner.cog import Cog
from beginner.models import set_database, PostgresqlDatabase
from beginner.scheduler import initialize_scheduler, schedule
from beginner.tags import tag
from datetime import datetime, timedelta
from discord.ext import commands
from functools import lru_cache
import discord
import os


class BeginnerCog(Cog):
    def __init__(self, client):
        self.client = client
        set_database(
            PostgresqlDatabase(
                "bpydb",
                user=os.environ.get("DB_USER", "postgresadmin"),
                host=os.environ.get("DB_HOST", "0.0.0.0"),
                port=os.environ.get("DB_PORT", "5432"),
                password=os.environ.get(
                    "DB_PASSWORD", "dev-env-password-safe-to-be-public"
                ),
            )
        )

    @Cog.listener()
    async def on_ready(self):
        initialize_scheduler()
        print("Bot is ready.")

    @Cog.command()
    async def d(self, ctx, message):
        if message == "bump":
            schedule(
                "disboard-bump-reminder",
                timedelta(hours=2),
                self.bump_reminder,
                no_duplication=True,
            )

    @tag("schedule", "disboard-bump")
    async def bump_reminder(self):
        channel = self.client.get_channel(644338578695913504)
        roundtable = self.get_role("roundtable")
        await channel.send(f"{roundtable.mention} It's been 2hrs since the last bump")

    @Cog.command()
    async def export(self, ctx, namespace):
        if len([r for r in ctx.author.roles if r.id == 644301991832453120]) == 0:
            return

        path = os.path.join("data", f"{namespace}.json")
        if not os.path.exists(path):
            await ctx.send(f"No such namespace: {namespace}")
        else:
            with open(path, "r") as json_file:
                await ctx.send(f"Here you go", file=discord.File(json_file))

    @Cog.command(name="import")
    async def import_(self, ctx, namespace):
        if len([r for r in ctx.author.roles if r.id == 644301991832453120]) == 0:
            return

        path = os.path.join("data", f"{namespace}.json")
        if not ctx.message.attachments:
            await ctx.send(f"Nothing attached to import")
        else:
            await ctx.message.attachments[0].save(path)
            self.client.unload_extension(f"beginner.cogs.{namespace}")
            self.client.load_extension(f"beginner.cogs.{namespace}")
            await ctx.send(
                f"Namespace {namespace} updated with contents of {ctx.message.attachments[0].filename}"
            )

    @staticmethod
    @lru_cache()
    def get_client() -> commands.Bot:
        client = commands.Bot(
            command_prefix="!",
            activity=discord.Activity(
                name="for '!help' to show you all commands",
                type=discord.ActivityType.watching,
            ),
        )
        client.remove_command("help")
        return client

    @staticmethod
    @lru_cache()
    def get_token():
        token = ""
        if "DISCORD_TOKEN" in os.environ:
            token = os.environ.get("DISCORD_TOKEN")
        elif BeginnerCog.is_dev_env() and os.path.exists("bot.token"):
            with open("bot.token", "r") as token_file:
                token = token_file.readline()
        if not token or len(token.strip()) != 59:
            message = [
                "No valid token could be found - Please set a token in your environment as DISCORD_TOKEN",
                f"\ttoken: {repr(token)}",
                f"\tdev: {BeginnerCog.is_dev_env()}",
            ]
            if BeginnerCog.is_dev_env():
                message.append(f"\tbot.token exists: {os.path.exists('bot.token')}")
            raise Exception("\n".join(message))
        return token.strip()

    @staticmethod
    @lru_cache()
    def is_dev_env():
        return not os.environ.get("PRODUCTION_BOT", False)

    @staticmethod
    def load_cogs(client):
        client.load_extension("beginner.cogs.google")
        client.load_extension("beginner.cogs.help")
        client.load_extension("beginner.cogs.python")
        client.load_extension("beginner.cogs.rules")
        client.load_extension("beginner.cogs.onboarding")

        if BeginnerCog.is_dev_env():
            import beginner.devcog

            client.add_cog(beginner.devcog.DevCog(client))

        client.add_cog(BeginnerCog(client))
