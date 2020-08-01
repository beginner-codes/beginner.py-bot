from beginner.cog import Cog
from beginner.colors import *
from beginner.scheduler import schedule
from beginner.tags import tag
from datetime import timedelta, datetime
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

        # Onboard all users who have been members for at least 48 hours
        for member in self.server.members:
            if role in member.roles:
                found += 1
                if await self.member_can_be_onboarded(member):
                    await member.remove_roles(role, reason="Onboard recently active member")
                    onboarding += 1

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

        channel = self.get_channel("rules")
        if reaction.channel_id != channel.id:
            return

        message = await channel.fetch_message(reaction.message_id)
        member = self.server.get_member(reaction.user_id)
        await message.remove_reaction("✅", member)
        await member.add_roles(
            self.get_role("coders"),
            self.get_role("new member"),
            reason="New member role assignment",
            atomic=True
        )


def setup(client):
    client.add_cog(OnBoarding(client))
