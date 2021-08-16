from typing import Optional
from beginner.cog import Cog, commands
from beginner.colors import *
from discord import Embed, Message, RawReactionActionEvent, PermissionOverwrite


class RoleAssignmentCog(Cog):
    def __init__(self, client):
        super().__init__(client)
        self.assignment_message: Optional[Message] = None
        self.reactions = {
            "📣": self.assign_announcements,
            "🗓": self.assign_events,
            "🤪": self.assign_off_topic,
        }

    @commands.command(name="create-role-assignment")
    @commands.has_guild_permissions(manage_guild=True)
    async def create_role_assignment(self, ctx):
        embed = (
            Embed(
                description=(
                    "React to this message to assign yourself the roles you're interested in. React again if you ever "
                    "want to remove the role."
                ),
                title="Role Assignment",
                color=YELLOW,
            )
            .add_field(
                name="📣 Announcements",
                value="React to this message with 📣 to be notified of server announcements.",
                inline=False,
            )
            .add_field(
                name="🗓 Events",
                value="React to this message with 🗓 to be notified of event updates.",
                inline=False,
            )
            .add_field(
                name="🤪 Off Topic",
                value=(
                    "React to this message with 🤪 to gain access to the hidden off topic channel. There are a few "
                    "special rules for anyone wanting to chat in that channel:\n\n"
                    "- No misinformation will be allowed. Be ready to provide **trustworthy** sources for any claims.\n"
                    "- Name calling and insults are **strictly** prohibited.\n"
                    "- **Safe for work** only."
                ),
                inline=False,
            )
        )
        message: Message = await self.find_assignment_message()
        if not message:
            message = await self.get_channel("role-assignment").send(embed=embed)
        else:
            await message.edit(embed=embed)

        await message.clear_reactions()
        for emoji in self.reactions:
            await message.add_reaction(emoji)

    @Cog.listener()
    async def on_raw_reaction_add(self, reaction: RawReactionActionEvent):
        channel = self.get_channel("role-assignment")
        if channel.id != reaction.channel_id:
            return

        if reaction.member.bot:
            return

        if not self.assignment_message:
            self.assignment_message = await self.find_assignment_message()

        if reaction.message_id != self.assignment_message.id:
            return

        if reaction.emoji.name in self.reactions:
            await self.reactions[reaction.emoji.name](reaction.member)

        await self.assignment_message.remove_reaction(reaction.emoji, reaction.member)

    async def assign_announcements(self, member):
        channel = self.get_channel("role-assignment")
        announcement = self.get_role("announcement")

        if announcement in member.roles:
            await member.remove_roles(announcement)
            await channel.send(
                f"{member.mention} you'll no longer be notified of announcements",
                delete_after=10,
            )
        else:
            await member.add_roles(announcement)
            await channel.send(
                f"{member.mention} you'll be notified of announcements",
                delete_after=10,
            )

    async def assign_events(self, member):
        channel = self.get_channel("role-assignment")
        event = self.get_role("event")

        if event in member.roles:
            await member.remove_roles(event)
            await channel.send(
                f"{member.mention} you'll no longer be notified of event updates",
                delete_after=10,
            )
        else:
            await member.add_roles(event)
            await channel.send(
                f"{member.mention} you'll be notified of event updates",
                delete_after=10,
            )

    async def assign_off_topic(self, member):
        channel = self.get_channel("role-assignment")
        off_topic = self.get_channel("🗞news-events-discussion")

        await off_topic.set_permissions(
            member, overwrite=PermissionOverwrite(read_messages=True)
        )

        await channel.send(
            f"{member.mention} you've been given access to {off_topic.mention}",
            delete_after=10,
        )

    async def find_assignment_message(self):
        channel = self.get_channel("role-assignment")
        messages = await channel.history(limit=2, oldest_first=True).flatten()
        if len(messages) >= 2:
            return messages[1]
        return None


def setup(client):
    client.add_cog(RoleAssignmentCog(client))
