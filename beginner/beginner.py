from beginner.cog import Cog
from beginner.scheduler import initialize_scheduler
from discord.ext import commands
from functools import lru_cache
import discord
import os


class BeginnerCog(Cog):
    @commands.Cog.listener()
    async def on_ready(self):
        self.logger.debug("Cog ready")
        initialize_scheduler(loop=self.client.loop)

        if not BeginnerCog.is_dev_env():
            await self.get_channel("bot-dev").send(
                f"Bot back online! Image Version: {os.environ.get('BOT_IMAGE_VERSION', 'NOT SET')}"
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
    def is_dev_env():
        return not os.environ.get("PRODUCTION_BOT", False)


def setup(client):
    client.add_cog(BeginnerCog(client))