from asyncio import sleep
from beginner.cog import Cog
from beginner.logging import create_logger
from beginner.models import set_database, PostgresqlDatabase
from beginner.scheduler import initialize_scheduler, schedule
from beginner.tags import tag
from datetime import datetime, timedelta
from discord.ext import commands
from functools import lru_cache
import discord
import logging
import os


class BeginnerCog(Cog):
    def __init__(self, client):
        super().__init__(client)
        user = os.environ.get("DB_USER", "postgresadmin")
        host = os.environ.get("DB_HOST", "0.0.0.0")
        port = os.environ.get("DB_PORT", "5432")
        mode = "require" if os.environ.get("PRODUCTION_BOT", False) else None
        self.logger.debug(
            f"\nConnecting to database:\n"
            f"- User {user}\n"
            f"- Host {host}\n"
            f"- Port {port}\n"
            f"- Mode {mode}"
        )
        set_database(
            PostgresqlDatabase(
                os.environ.get("DB_NAME", "bpydb"),
                user=user,
                host=host,
                port=port,
                password=os.environ.get(
                    "DB_PASSWORD", "dev-env-password-safe-to-be-public"
                ),
                sslmode=mode,
            )
        )
        initialize_scheduler(loop=client.loop)

    @commands.Cog.listener()
    async def on_ready(self):
        self.logger.debug("Cog ready")
        if not BeginnerCog.is_dev_env():
            await self.get_channel("bot-dev").send(
                f"Bot back online! Image Version: {self.settings.get('BOT_IMAGE_VERSION', 'NOT SET')}"
            )

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
        if BeginnerCog.is_dev_env():
            import beginner.devcog

            client.add_cog(beginner.devcog.DevCog(client))

        BeginnerCog.load_extension(client, "beginner.cogs.user_roles")
        BeginnerCog.load_extension(client, "beginner.cogs.repeater")
        BeginnerCog.load_extension(client, "beginner.cogs.google")
        BeginnerCog.load_extension(client, "beginner.cogs.help")
        BeginnerCog.load_extension(client, "beginner.cogs.python")
        BeginnerCog.load_extension(client, "beginner.cogs.rules")
        BeginnerCog.load_extension(client, "beginner.cogs.onboarding")
        BeginnerCog.load_extension(client, "beginner.cogs.spam")
        BeginnerCog.load_extension(client, "beginner.cogs.statistics")
        BeginnerCog.load_extension(client, "beginner.cogs.tips")
        BeginnerCog.load_extension(client, "beginner.cogs.moderation")
        BeginnerCog.load_extension(client, "beginner.cogs.bumping")
        BeginnerCog.load_extension(client, "beginner.cogs.challenges")
        BeginnerCog.load_extension(client, "beginner.cogs.code_runner")
        BeginnerCog.load_extension(client, "beginner.cogs.settings")
        BeginnerCog.load_extension(client, "beginner.cogs.fun")
        BeginnerCog.load_extension(client, "beginner.cogs.candidates")
        BeginnerCog.load_extension(client, "beginner.cogs.help_rotator")
        client.add_cog(BeginnerCog(client))

    @staticmethod
    def load_extension(client, name, *args, dev_only=False, **kwargs):
        if dev_only and not BeginnerCog.is_dev_env():
            create_logger().debug(f"{name} is disabled in production")
            return

        if os.environ.get(name, 1) == "0":
            create_logger().debug(f"{name} is disabled")
            return

        return client.load_extension(name, *args, **kwargs)

    @staticmethod
    def setup_logging():
        logging.basicConfig(
            format="%(asctime)s: %(levelname)-9s %(name)-16s ::          %(message)s",
            datefmt="%m/%d/%Y %I:%M:%S %p",
            level=logging.ERROR,
        )

        logging.getLogger("beginnerpy").setLevel(logging.DEBUG)
