import os

import beginner.kudos as kudos
from beginner.cog import Cog


class Kudos(Cog):
    def __init__(self, client):
        self.dev_author = int(os.environ.get("DEV_AUTHOR_ID", 0))
        self._reactions = {}
        self._multipliers = {"good": 1, "great": 2, "excellent": 3}
        super().__init__(client)

    @property
    def reactions(self):
        if not self._reactions:
            self._reactions = {
                "good": self.get_emoji("beginner"),
                "great": self.get_emoji("intermediate"),
                "excellent": self.get_emoji("expert"),
            }
            self._reactions.update(
                {emoji.id: name for name, emoji in self.reactions.items()}
            )
        return self._reactions

    @Cog.command()
    async def kudos(self, ctx):
        if self.dev_author and ctx.author.id != self.dev_author:
            return

        if ctx.author.bot:
            return

        author_kudos = kudos.get_user_kudos(ctx.author.id)
        message = [
            f"{ctx.author.mention} you have {author_kudos if author_kudos > 0 else 'no'} kudos"
        ]
        for index, (member_id, member_kudos) in enumerate(kudos.get_highest_kudos(3)):
            member = self.server.get_member(member_id)
            name = member.display_name if member else "*Old Member*"
            message.append(f"{index + 1}. {name} has {member_kudos} kudos")

        await ctx.send("\n".join(message))

    @Cog.listener()
    async def on_raw_reaction_add(self, reaction):
        if self.dev_author and reaction.user_id != self.dev_author:
            return

        if reaction.emoji.id not in self.reactions:
            return

        channel = self.server.get_channel(reaction.channel_id)
        message = await channel.fetch_message(reaction.message_id)

        print(kudos.get_last_kudos_given(reaction.user_id, message.author.id))

        if message.author.id == reaction.user_id:
            # Remove all kudos reactions a user tries to give them self
            await self.clear_previous_kudos(message, reaction.member, True)
            return

        level = self.reactions[reaction.emoji.id]
        await self.clear_previous_kudos(message, reaction.member, level)
        kudos.remove_kudos(reaction.message_id, reaction.user_id)

        kudos_points = 2 ** self._multipliers[level]
        kudos.give_user_kudos(
            kudos_points, message.author.id, reaction.user_id, message.id
        )

    @Cog.listener()
    async def on_raw_reaction_remove(self, reaction):
        if self.dev_author and reaction.user_id != self.dev_author:
            return

        if reaction.emoji.id not in self.reactions:
            return

        channel = self.server.get_channel(reaction.channel_id)
        message = await channel.fetch_message(reaction.message_id)

        if message.author == reaction.user_id and not self.dev_author:
            return

        kudos.remove_kudos(reaction.message_id, reaction.user_id)

    async def clear_previous_kudos(self, message, user, giving):
        for reaction in message.reactions:
            if isinstance(reaction.emoji, str):
                continue

            kudos_level = self.reactions.get(reaction.emoji.id, False)
            if not kudos_level or kudos_level == giving:
                continue

            await reaction.remove(user)


def setup(client):
    client.add_cog(Kudos(client))
