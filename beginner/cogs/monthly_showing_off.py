from beginner.logging import get_logger
from discord.ext.commands import Cog, Context, command


class MonthlyShowingOffCog(Cog):
    """Cog for the monthly showing off challenge!"""

    def __init__(self, client):
        self.client = client
        self.log = get_logger(("beginner.py", self.__class__.__name__))

    @Cog.listener()
    async def on_ready(self):
        self.log.debug(f"{type(self).__name__} is ready")


def setup(client):
    client.add_cog(MonthlyShowingOffCog(client))
