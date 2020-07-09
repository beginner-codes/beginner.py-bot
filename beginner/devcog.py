from beginner.cog import Cog
import os


class DevCog(Cog):
    def __init__(self, client):
        super().__init__(client)
        self.load_env()

    def load_env(self):
        if os.path.exists("bot.config"):
            self.logger.debug("Loading config file")
            with open("bot.config") as config:
                for line in config:
                    key, value = line.split("=")
                    os.environ[key.strip()] = value.strip()

    @Cog.command()
    async def load(self, ctx, *extensions):
        if (
            extensions
            and len([r for r in ctx.author.roles if r.id == 644301991832453120]) > 0
        ):
            for extension in extensions:
                try:
                    self.client.load_extension(f"beginner.cogs.{extension}")
                    self.logger.debug(f"Loaded extension {extension}")
                except:
                    self.logger.debug(f"FAILED to load extension {extension}")
            await ctx.send(
                f"{ctx.author.display_name} loaded these cogs: {', '.join(extensions)}"
            )

    @Cog.command()
    async def unload(self, ctx, *extensions):
        if (
            extensions
            and len([r for r in ctx.author.roles if r.id == 644301991832453120]) > 0
        ):
            for extension in extensions:
                try:
                    self.client.unload_extension(f"beginner.cogs.{extension}")
                    self.logger.debug(f"Unloaded extension {extension}")
                except:
                    self.logger.debug(f"FAILED to unload extension {extension}")
            await ctx.send(
                f"{ctx.author.display_name} unloaded these cogs: {', '.join(extensions)}"
            )

    @Cog.command()
    async def reload(self, ctx, *extensions):
        if (
            extensions
            and len([r for r in ctx.author.roles if r.id == 644301991832453120]) > 0
        ):
            for extension in extensions:
                try:
                    self.client.unload_extension(f"beginner.cogs.{extension}")
                    self.client.load_extension(f"beginner.cogs.{extension}")
                    self.logger.debug(f"Reloaded extension {extension}")
                except:
                    self.logger.debug(f"FAILED to reload extension {extension}")
            await ctx.send(
                f"{ctx.author.display_name} reloaded these cogs: {', '.join(extensions)}"
            )


def setup(client):
    client.add_cog(DevCog(client))
