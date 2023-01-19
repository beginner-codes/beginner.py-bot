from beginner.cog import Cog, commands
from beginner.colors import *
from beginner.scheduler import schedule
from beginner.tags import tag
from datetime import timedelta
import ast
import nextcord
import nextcord.ext.commands


HELP_INSTRUCTIONS_POST_ID = 1065670718337069127


class HelpPosts(Cog):
    @Cog.listener()
    async def on_message(self, message: nextcord.Message):
        if message.author.id == self.client.user.id:
            return

        if message.channel.id != HELP_INSTRUCTIONS_POST_ID:
            return

        await message.delete()
        await message.channel.send(
            f"{message.author.mention} your message has been deleted. Please read the instructions above.",
            delete_after=10,
        )


def setup(client):
    client.add_cog(HelpPosts(client))
