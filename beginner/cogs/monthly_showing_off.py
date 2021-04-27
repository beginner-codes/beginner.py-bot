from discord.ext.commands import Cog, Context, command


class MonthlyShowingOffCog(Cog):
    """Cog for the monthly showing off challenge!"""

    ...


def setup(client):
    client.add_cog(MonthlyShowingOffCog(client))
