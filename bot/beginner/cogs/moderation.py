from beginner.cog import Cog

# from beginner.models.messages import ModAction, ModActionTypes
import discord
from discord import Embed, Message, Member
from beginner.cogs.rules import RulesCog


class ModerationCog(Cog):
    @Cog.command(name="warn")
    async def warn(self, ctx, user, *, reason: str):
        if not (
            set(ctx.author.roles) & {self.get_role("Roundtable"), self.get_role("mods")}
        ):
            return

        embed = Embed(description=reason, color=0xCC2222)
        embed.set_author(name="Mod Warning", icon_url=self.server.icon_url)
        member = self.server.get_member(int(user[3:-1]))

        if reason.find(" ") == -1:
            rule = RulesCog.get_rule(reason, fuzzy=True)
            if rule:
                embed.description = rule.message
                embed.set_author(
                    name=f"Mod Warning: {rule.title}", icon_url=self.server.icon_url
                )

        embed.set_footer(text=ctx.author.display_name, icon_url=ctx.author.avatar_url)
        message = await ctx.send(embed=embed)
        successfully_dmd = await self.send_dm(
            member,
            embed,
            ctx.message,
            "You've received a moderator warning on the Beginner.py server.",
        )
        if not successfully_dmd:
            reason += "\n*Unable to DM user*"

        await self.log_action("WARN", member, ctx.author, reason, message)

    async def send_dm(
        self, member: Member, embed: Embed, message: Message, description: str
    ):
        embed.description = (
            f"{description}\n\n"
            f"Reason: {embed.description}\n\n"
            f"[Jump To Conversation]({message.jump_url})"
        )
        try:
            await member.send(embed=embed)
            return True
        except discord.errors.Forbidden:
            return False

    async def log_action(
        self, action: str, user: Member, mod: Member, reason: str, message: Message
    ):
        await self.get_channel("activity-log").send(
            embed=Embed(
                description=f"Moderator: {mod.mention}\n"
                f"User: {user.mention}\n"
                f"Reason: {reason}\n\n"
                f"[Jump To Action]({message.jump_url})",
                color=0xCC2222,
            ).set_author(
                name=f"{action} @{user.display_name}", icon_url=self.server.icon_url
            )
        )


def setup(client):
    client.add_cog(ModerationCog(client))
