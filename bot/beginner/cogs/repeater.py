from beginner.cog import Cog
from discord import Embed, Status
import logging


class RepeaterCog(Cog):
    @Cog.listener()
    async def on_ready(self):
        logging.debug("Repeater is ready")

    @Cog.command()
    async def send(self, ctx, channel, *, message):
        if not ctx.author.guild_permissions.manage_guild:
            return

        title = (
            message[: message.find("\n")] if message.find("\n") > 0 else "beginner.py"
        )
        content = message[message.find("\n") + 1 :]

        embed = (
            Embed(description=content, color=0x306998)
            .set_author(name=title, icon_url=self.server.icon_url)
            .set_footer(text=ctx.author.display_name, icon_url=ctx.author.avatar_url)
        )
        await self.server.get_channel(int(channel[2:-1])).send(embed=embed)


def setup(client):
    client.add_cog(RepeaterCog(client))
