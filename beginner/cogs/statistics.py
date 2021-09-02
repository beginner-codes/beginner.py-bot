from beginner.cog import Cog
from nextcord import Embed, Status


class StatisticsCog(Cog):
    @Cog.listener()
    async def on_ready(self):
        self.logger.info(
            f"Found {self.get_online():,} online of {self.server.member_count:,} members"
        )

    @Cog.command()
    async def stats(self, ctx):
        num_bots = self.get_bots()
        await ctx.send(
            embed=Embed(
                title=f"Server Stats",
                description=(
                    f"There are currently {self.get_online():,} coders online of "
                    f"{self.server.member_count - num_bots:,} coders!!!\n\n{self.get_pending():,} have not accepted "
                    f"the rules. Found {num_bots:,} bots."
                ),
                color=0x00A35A,
            )
        )

    def get_bots(self) -> int:
        return sum(1 for member in self.server.members if member.bot)

    def get_pending(self) -> int:
        return sum(1 for member in self.server.members if member.pending)

    def get_online(self) -> int:
        return sum(
            1
            for member in self.server.members
            if member.status != Status.offline and not member.bot
        )


def setup(client):
    client.add_cog(StatisticsCog(client))
