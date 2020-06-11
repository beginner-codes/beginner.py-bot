from beginner.cog import Cog, commands
from discord import Member, Role
import asyncio


class CandidatesCog(Cog):
    async def cog_command_error(self, ctx, error):
        print("Command error:", error)

    @Cog.command()
    @commands.has_role("Jedi Council")
    async def candidate(self, ctx, member: Member, role: str = "helper"):
        candidates_channel = self.get_channel(self.settings.get("CANDIDATES_CHANNEL", "candidates"))
        if candidates_channel.id != ctx.message.channel.id:
            return

        if role.casefold().rstrip("s") not in {"mod", "helper"}:
            await ctx.send(f"The role must be either 'helper' or 'mod', got '{role}'")
            return

        await member.add_roles(self.get_role(self.settings.get("CANDIDATES_ROLE", "candidate")))
        await ctx.send(f"{member.mention} you've been invited to join our team as a {role}. What do you say?")

    @Cog.command()
    @commands.has_role("Jedi Council")
    async def thanks(self, ctx, member: Member):
        candidates_channel = self.get_channel(self.settings.get("CANDIDATES_CHANNEL", "candidates"))
        if candidates_channel.id != ctx.message.channel.id:
            return

        candidate_role = self.get_role(self.settings.get("CANDIDATES_ROLE", "candidate"))
        if candidate_role not in member.roles:
            return

        await ctx.send(f"{member.mention} thank you for your interest! You'll be removed from this channel shortly.")
        await asyncio.sleep(10)
        await member.remove_roles(candidate_role)
        await ctx.send(f"{member.mention} has been removed from {candidates_channel.mention}!")

    @Cog.command()
    @commands.has_role("Jedi Council")
    async def make(self, ctx, member: Member, role: Role):
        candidates_channel = self.get_channel(self.settings.get("CANDIDATES_CHANNEL", "candidates"))
        if candidates_channel.id != ctx.message.channel.id:
            return

        candidate_role = self.get_role(self.settings.get("CANDIDATES_ROLE", "candidate"))
        mod_role = self.get_role(self.settings.get("MODERATOR_ROLE", "mods"))
        helper_role = self.get_role(self.settings.get("HELPER_ROLE", "helpers"))
        council_role = self.get_role(self.settings.get("COUNCIL_ROLE", "Jedi Council"))
        if candidate_role not in member.roles:
            await ctx.send(f"{member.mention} is not a candidate.")
            return

        if role not in {helper_role, mod_role, council_role}:
            await ctx.send(f"{role.name} is not a valid helper or moderator role.")
            return

        await member.remove_roles(candidate_role)
        await member.add_roles(role)
        await ctx.send(f"{member.mention} has been added to the {role.mention} role!")

    @Cog.command()
    @commands.has_role("Jedi Council")
    async def unmake(self, ctx, member: Member, role: Role):
        candidates_channel = self.get_channel(self.settings.get("CANDIDATES_CHANNEL", "candidates"))
        if candidates_channel.id != ctx.message.channel.id:
            return

        mod_role = self.get_role(self.settings.get("MODERATOR_ROLE", "mods"))
        helper_role = self.get_role(self.settings.get("HELPER_ROLE", "helpers"))
        council_role = self.get_role(self.settings.get("COUNCIL_ROLE", "Jedi Council"))
        if role not in member.roles:
            await ctx.send(f"{member.mention} does not have the {role.name} role.")
            return

        if role not in {helper_role, mod_role, council_role}:
            await ctx.send(f"{role.name} is not a valid helper or moderator role.")
            return

        await member.remove_roles(role)
        await ctx.send(f"{member.mention} has been removed from the {role.mention} role.")


def setup(client):
    client.add_cog(CandidatesCog(client))
