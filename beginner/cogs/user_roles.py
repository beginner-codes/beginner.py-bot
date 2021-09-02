from beginner.cog import Cog
from nextcord import Embed, Status
import logging


class UserRolesCog(Cog):
    def __init__(self, client):
        super().__init__(client)
        self.channel = None
        self.reactions_to_roles = {}

    @Cog.listener()
    async def on_ready(self):
        logging.debug("Cog ready")
        self.channel = self.get_channel("role-assignment")
        message = await self.get_message()

        # Load the roles
        self.reactions_to_roles = {
            "beginner": self.get_role("beginners"),
            "intermediate": self.get_role("intermediates"),
            "expert": self.get_role("experts"),
        }

    @Cog.listener()
    async def on_raw_reaction_add(self, reaction):
        member = self.server.get_member(reaction.user_id)
        message = await self.get_message()

        if member.bot:
            return

        if reaction.message_id != message.id:
            return

        if reaction.emoji.name not in self.reactions_to_roles:
            await message.remove_reaction(reaction.emoji, member)
            return

        await self.assign_members_role(
            self.reactions_to_roles[reaction.emoji.name], member
        )
        await self.remove_reactions(reaction.emoji.name, member)
        await self.channel.send(
            f"{member.mention} you've been assigned the role {reaction.emoji.name}",
            delete_after=10,
        )

    @Cog.listener()
    async def on_raw_reaction_remove(self, reaction):
        member = self.server.get_member(reaction.user_id)
        message = await self.get_message()
        if member.bot:
            return

        if reaction.message_id != message.id:
            return

        if reaction.emoji.name not in self.reactions_to_roles:
            await message.remove_reaction(reaction.emoji, member)
            return

        await member.remove_roles(self.reactions_to_roles[reaction.emoji.name])
        await self.channel.send(
            f"{member.mention} you've been removed from the {reaction.emoji.name} role",
            delete_after=10,
        )

    async def add_reactions(self):
        message = await self.get_message()
        await message.add_reaction(self.get_emoji("beginner"))
        await message.add_reaction(self.get_emoji("intermediate"))
        await message.add_reaction(self.get_emoji("expert"))

    async def assign_members_role(self, role, member):
        await member.remove_roles(*self.reactions_to_roles.values())
        await member.add_roles(role)

    async def get_message(self):
        messages = await self.channel.history(limit=1, oldest_first=True).flatten()
        message = None

        # Load the message from the channel, creating if necessary
        if not messages:
            message_content = (
                f"**Select your coding skill level by reacting to this message**\n\n"
                f"Use {self.get_emoji('beginner')} if you're a beginner\n"
                f"Use {self.get_emoji('intermediate')} if you're at an intermediate skill level\n"
                f"Use {self.get_emoji('expert')} if you're an expert (e.g. production work experience)\n"
            )
            embed = Embed(description=message_content, color=0x306998).set_author(
                name=f"Skill Level Assignment", icon_url=self.server.icon_url
            )
            embed.set_footer(
                text="We reserve the right to adjust your skill level manually if "
                "we don't feel you've been honest about it."
            )
            message = await self.channel.send(embed=embed)
            await self.add_reactions()
        else:
            message = messages[0]

        return message

    async def remove_reactions(self, keep_reaction, member):
        for emoji in self.reactions_to_roles:
            if emoji != keep_reaction:
                message = await self.get_message()
                await message.remove_reaction(self.get_emoji(emoji), member)


def setup(client):
    client.add_cog(UserRolesCog(client))
