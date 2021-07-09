from beginner.cog import Cog
from discord import Embed
from enum import Enum


class StatisticsCog(Cog):
    @Cog.command()
    async def stats(self, ctx):
        bots = [member for member in self.server.members if member.bot]
        message = (
            f"There are currently {self.get_online()} coders online "
            f"of {self.server.member_count - len(bots)} coders!!!"
            f"\n\n{self.get_pending()} have not accepted the rules, {len(bots)} bots\n```"
        )
        embed = Embed(title=f"Server Stats", description=message, color=0x00A35A)
        await ctx.send(embed=embed)

    def get_pending(self) -> int:
        return sum(1 for member in self.server.members if member.pending)

    def get_online(self) -> int:
        return sum(1 for member in self.server.members if member.status.online)


def setup(client):
    client.add_cog(StatisticsCog(client))
