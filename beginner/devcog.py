from beginner.cog import Cog


class DevCog(Cog):
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
