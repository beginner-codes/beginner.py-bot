from beginner.cog import Cog
from beginner.colors import *
from beginner.scheduler import schedule
from beginner.tags import tag
from datetime import timedelta, datetime
import asyncio
import discord


class OnBoarding(Cog):
    async def ready(self):
        self.schedule_onboarding()

    def schedule_onboarding(self):
        now_utc = datetime.utcnow()
        next_onboarding = (now_utc + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        schedule("new-member-onboarding", next_onboarding, self.onboard_new_members, no_duplication=True)

    @tag("schedule", "onboard-new-members")
    async def onboard_new_members(self):
        self.logger.debug("Onboarding new members")

        found = 0
        onboarding = 0
        role = self.get_role("new member")

        # Find all users who can be onboarded
        removing = []
        for member in self.server.members:
            if role in member.roles:
                found += 1
                if await self.member_can_be_onboarded(member):
                    removing.append(member.remove_roles(role, reason="Onboard recently active member"))
                    onboarding += 1

        # Remove new member roles
        await asyncio.gather(*removing)

        # Log results
        self.logger.debug(f"Found {found} new members, {onboarding} were onboarded")
        await self.get_channel("mod-action-log").send(
            embed=discord.Embed(
                color=BLUE,
                description=f"Found {found} new members, {onboarding} were onboarded"
            ).set_author(name="Onboarding New Members", icon_url=self.server.icon_url)
        )

        # Schedule next onboarding
        self.schedule_onboarding()

    async def member_can_be_onboarded(self, member: discord.Member):
        return (datetime.utcnow() - member.joined_at).days >= 2

    @Cog.listener()
    async def on_raw_reaction_add(self, reaction):
        if reaction.emoji.name != "✅":
            return

        channel = self.get_channel("new-users")
        if reaction.channel_id != channel.id:
            return

        message = await channel.fetch_message(reaction.message_id)
        if message.mentions and message.mentions[0].id == reaction.user_id:
            await self.server.get_member(reaction.user_id).add_roles(
                self.get_role("coders"),
                self.get_role("new member"),
                reason="New member role assignment"
            )
            await message.delete()

    @Cog.listener()
    async def on_member_join(self, member):
        await self._send_welcome_message(member.id)

    @tag("schedule", "welcome-message")
    async def _send_welcome_message(self, member_id):
        member = self.server.get_member(member_id)
        emote = "✅"
        rules = self.get_channel("rules")
        message = await self.get_channel("new-users").send(
            f"Welcome {member.mention}!!! Have a look at <#{rules.id}>, once you're done tap the {emote} below to "
            f"agree to the rules and gain full access to the server!"
        )
        await message.add_reaction(emote)

    @Cog.listener()
    async def on_member_remove(self, member):
        await self.get_channel("new-users").purge(
            limit=1, check=lambda message: message.content.find(f"<@{member.id}>") >= 0
        )


def setup(client):
    client.add_cog(OnBoarding(client))
