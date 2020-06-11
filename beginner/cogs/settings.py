from beginner.cog import Cog
from ast import literal_eval


class Settings(Cog):
    @Cog.command()
    async def setvalue(self, ctx, raw_name, *, raw_value):
        if self.get_role("jedi council") not in ctx.author.roles:
            return

        try:
            value = literal_eval(raw_value.strip())
        except Exception as ex:
            await ctx.send(f"Failed to set value\n```\n{ex}\n```")
        else:
            name = raw_name.strip()
            self.settings[name] = value
            await ctx.send(f"```\n{name} = {repr(value)}```")

    @Cog.command()
    async def getvalue(self, ctx, raw_name):
        if self.get_role("jedi council") not in ctx.author.roles:
            return

        name = raw_name.strip()
        value = self.settings[name]
        await ctx.send(f"```\n{name} = {repr(value)}```")

    @Cog.command()
    async def listvalues(self, ctx):
        if self.get_role("jedi council") not in ctx.author.roles:
            return

        await ctx.send("\n".join(f"`{name} = {repr(value)}`" for name, value in self.settings.all().items()))


def setup(client):
    client.add_cog(Settings(client))
