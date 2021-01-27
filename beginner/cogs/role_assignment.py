from typing import Optional
from beginner.cog import Cog, commands
from discord import Embed, Message, RawReactionActionEvent, PermissionOverwrite


class RoleAssignmentCog(Cog):
    def __init__(self, client):
        super().__init__(client)
        self.assignment_message: Optional[Message] = None

    @commands.command(name="create-pol-assignment")
    @commands.has_guild_permissions(manage_guild=True)
    async def create_role_assignment(self, ctx):
        message = await self.get_channel("role-assignment").send(
            embed=Embed(
                description=(
                    "React to this message to gain access to the hidden off topic channel. There are a few special "
                    "rules for anyone wanting to chat in that channel:\n\n"
                    "- No misinformation will be allowed. Be ready to provide **trustworthy** sources for any claims.\n"
                    "- Name calling and insults are **strictly** prohibited.\n"
                    "- **Safe for work** only."
                ),
                title="Off Topic",
            )
        )
        await message.add_reaction("✅")

    @Cog.listener()
    async def on_raw_reaction_add(self, reaction: RawReactionActionEvent):
        channel = self.get_channel("role-assignment")
        if channel.id != reaction.channel_id:
            return

        if reaction.member.bot:
            return

        if not self.assignment_message:
            self.assignment_message: Message = (
                await channel.history(limit=2, oldest_first=True).flatten()
            )[1]

        if reaction.message_id != self.assignment_message.id:
            return

        off_topic = self.get_channel("🤠wild-west-off-topic")
        await off_topic.set_permissions(
            reaction.member, overwrite=PermissionOverwrite(read_messages=True)
        )

        await self.assignment_message.remove_reaction(reaction.emoji, reaction.member)
        await channel.send(
            f"{reaction.member.mention} you've been given access to {off_topic.mention}",
            delete_after=10,
        )


def setup(client):
    client.add_cog(RoleAssignmentCog(client))
