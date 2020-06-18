from beginner.cog import Cog, commands
from ast import literal_eval


class Settings(Cog):
    @Cog.command()
    @commands.has_guild_permissions(manage_messages=True)
    async def setvalue(self, ctx, raw_name, *, raw_value):
        try:
            value = literal_eval(raw_value.strip())
        except Exception as ex:
            await ctx.send(f"Failed to set value\n```\n{ex}\n```")
        else:
            name = raw_name.strip()
            self.settings[name] = value
            await ctx.send(f"```\n{name} = {repr(value)}```")

    @Cog.command()
    @commands.has_guild_permissions(manage_messages=True)
    async def getvalue(self, ctx, raw_name):
        name = raw_name.strip()
        value = self.settings[name]
        await ctx.send(f"```\n{name} = {repr(value)}```")

    @Cog.command()
    @commands.has_guild_permissions(manage_messages=True)
    async def listvalues(self, ctx):
        await ctx.send(
            "\n".join(
                f"`{name} = {repr(value)}`" for name, value in self.settings.all().items() if not name.startswith("_")
            )
        )


def setup(client):
    client.add_cog(Settings(client))
