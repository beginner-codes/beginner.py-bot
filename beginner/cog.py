from discord.ext import commands


class Cog(commands.Cog):
    @staticmethod
    def command(*args, **kwargs):
        return commands.command(*args, **kwargs)
