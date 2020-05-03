from beginner.cog import Cog
from beginner.cogs.rules import RulesCog
from beginner.scheduler import schedule
from datetime import timedelta
from discord import Embed, Message, Member
from beginner.tags import tag
import discord


class ModerationCog(Cog):
    @Cog.command(name="mute")
    async def mute(self, ctx, user, duration, *, reason: str):
        if not (
            set(ctx.author.roles) & {self.get_role("roundtable"), self.get_role("mods")}
        ):
            return

        member: Member = self.server.get_member(self.parse_user_id(user))
        if self.get_role("muted") in member.roles:
            await ctx.send(f"*{member.mention} is already muted*")
            return

        minutes = self.parse_duration(duration)
        embed = self.build_mod_action_embed(
            ctx, member, reason, f"Muted for {self.format_duration(minutes)}"
        )
        message = await ctx.send(embed=embed)

        successfully_dmd = await self.send_dm(
            member, embed, ctx.message, "You've been muted on the Beginner.py server.\n"
        )
        if not successfully_dmd:
            reason += "\n*Unable to DM user*"

        await self.log_action(
            "MUTE",
            member,
            ctx.author,
            reason,
            message,
            Duration=self.format_duration(minutes),
        )

        schedule(
            "unmute-member", timedelta(minutes=minutes), self.unmute_member, member.id
        )

        await member.add_roles(self.get_role("muted"), reason="Mod Mute")

    @Cog.command(name="unmute")
    async def unmute(self, ctx, user):
        if not (
            set(ctx.author.roles) & {self.get_role("roundtable"), self.get_role("mods")}
        ):
            return

        member: Member = self.server.get_member(int(user[3:-1]))
        await member.remove_roles(self.get_role("muted"), reason="Mod unmute")

        await ctx.send(f"*{member.mention} is unmuted*")

    @Cog.command(name="warn")
    async def warn(self, ctx, user, *, reason: str):
        if not (
            set(ctx.author.roles) & {self.get_role("Roundtable"), self.get_role("mods")}
        ):
            return

        member = self.server.get_member(self.parse_user_id(user))
        embed = self.build_mod_action_embed(ctx, member, reason, "Mod Warning")
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
        self,
        action: str,
        user: Member,
        mod: Member,
        reason: str,
        message: Message,
        **kwargs,
    ):
        additional_fields = "\n".join(
            [f"{key}: {value}" for key, value in kwargs.items()]
        )
        await self.get_channel("activity-log").send(
            embed=Embed(
                description=f"Moderator: {mod.mention}\n"
                f"User: {user.mention}\n"
                f"Reason: {reason}"
                + ("\n" if additional_fields else "")
                + f"{additional_fields}\n\n"
                f"[Jump To Action]({message.jump_url})",
                color=0xCC2222,
            ).set_author(
                name=f"{action} @{user.display_name}", icon_url=self.server.icon_url
            )
        )

    def build_mod_action_embed(
        self, ctx, user: Member, reason: str, title: str
    ) -> Embed:
        embed = Embed(description=reason, color=0xCC2222)
        self.get_rule_for_reason(reason, embed)
        embed.description = f"{user.mention}\n{embed.description}"
        embed.set_author(name=title, icon_url=self.server.icon_url)
        embed.set_footer(text=ctx.author.display_name, icon_url=ctx.author.avatar_url)
        return embed

    def format_duration(self, minutes: int) -> str:
        result = []
        if minutes > 24 * 60:
            days = minutes // (24 * 60)
            result.append(f"{days} day{'s' if days > 1 else ''}")
            minutes -= days * 24 * 60

        if minutes > 60:
            hours = minutes // 60
            result.append(f"{hours} hour{'s' if hours > 1 else ''}")
            minutes -= hours * 60

        if minutes > 0:
            result.append(f"{minutes} minute{'s' if minutes > 1 else ''}")

        return " ".join(result)

    def get_rule_for_reason(self, reason: str, embed: Embed):
        if reason.find(" ") == -1:
            rule = RulesCog.get_rule(reason, fuzzy=True)
            if rule:
                embed.description = f"**{rule.title}**\n{rule.message}"
                embed.set_author(name=f"Mod Warning", icon_url=self.server.icon_url)

    def parse_duration(self, duration: str):
        if duration.endswith("d"):
            return int(duration[:-1]) * 24 * 60

        elif duration.endswith("h"):
            return int(duration[:-1]) * 60

        return int(duration[:-1] if duration.endswith("m") else duration)

    def parse_user_id(self, user_tag: str) -> int:
        return int(user_tag[3:-1] if user_tag.find("!") >= 0 else user_tag[2:-1])

    @tag("schedule", "unmute-member")
    async def unmute_member(self, member_id):
        member: Member = self.server.get_member(member_id)
        await member.remove_roles(self.get_role("muted"), reason="Mute expired")


def setup(client):
    client.add_cog(ModerationCog(client))
