from beginner.cog import Cog, commands
from beginner.cogs.rules import RulesCog
from beginner.models.mod_actions import ModAction
from beginner.scheduler import schedule
from datetime import timedelta, datetime
from discord import Embed, Message, Member, User
from beginner.tags import tag
import discord
import pickle
import re


class ModerationCog(Cog):
    async def cog_command_error(self, ctx, error):
        print("Command error:", error)

    @Cog.listener()
    async def on_member_join(self, member: Member):
        history = list(
            ModAction.select().limit(1).where(ModAction.user_id == member.id)
        )
        if history:
            mod_action_log = self.get_channel(
                self.settings.get("MOD_ACTION_LOG_CHANNEL", "mod-action-log")
            )
            await mod_action_log.send(
                embed=Embed(
                    description=f"{member.mention} has rejoined. They have a past history of mod actions.",
                    color=0xFFE873,
                ).set_author(name="Member Rejoined")
            )

    @Cog.command(name="lookup")
    @commands.has_guild_permissions(manage_messages=True)
    async def lookup(self, ctx, username_part: str):
        members = []
        name_part = username_part.casefold()
        user_id = int(username_part) if username_part.isdigit() else 0
        for member in self.server.members:
            display_name = member.name.casefold() if member.name else ""
            nick = member.nick.casefold() if member.nick else ""
            if user_id and member.id == user_id:
                members.append(member)
            if name_part in display_name or name_part in nick:
                members.append(member)

        message = (
                f"Found {len(members)} members with names that contain '{username_part}'\n"
                + "\n".join(
                    (
                        f"-  **{member.name}#{member.discriminator}**  ({member.nick if member.nick else '*No Nick Name*'})\n"
                        f"   Joined {member.joined_at: %b %-d %Y}\n"
                        f"   Top Role `@{member.top_role.name.strip('@')}`\n"
                        f"   {member.id}"
                    )
                    for member in members[:15]
                )
                + (f"\n\n*There are {len(members) - 15} more members who matched*" if len(members) - 15 > 0 else "")
        )

        await ctx.send(message)


    @Cog.command(name="ban")
    @commands.has_guild_permissions(manage_messages=True)
    async def ban(self, ctx, user_detail: str, *, reason=None):
        if not reason:
            await ctx.send(
                "You must provide a reason for the ban. `!ban [@user|1234] reason for ban`"
            )
            return

        user_id = re.findall("\d+", user_detail)
        if user_id:
            user_id = user_id[0]
        else:
            await ctx.send("Invalid user ID was provided:", user_detail)
            return

        member = self.server.get_member(int(user_id))
        if not member:
            await ctx.send("No such member found")
            return

        if member.guild_permissions.manage_messages:
            await ctx.send(
                "You cannot ban this user", delete_after=15
            )
            return

        embed = self.build_mod_action_embed(ctx, member, reason, f"You've Been Banned")
        successfully_dmd = await self.send_dm(
            member,
            embed,
            description="You've been banned from the Beginner.py server.\n",
        )
        if not successfully_dmd:
            reason += "\n*Unable to DM user*"

        await self.server.ban(member, reason=reason, delete_message_days=0)

        await ctx.send(f"{member.display_name} has been banned")
        await self.log_action("Ban", member, ctx.author, reason, ctx.message)
        self.save_action(
            "BAN", member, ctx.author, message=reason, reference=ctx.message.id
        )

    @Cog.command(name="kick")
    @commands.has_guild_permissions(manage_messages=True)
    async def kick(self, ctx, user_detail: str, *, reason=None):
        if not reason:
            await ctx.send(
                "You must provide a reason for the kick. `!kick [@user|1234] reason for kick`"
            )
            return

        user_id = re.findall("\d+", user_detail)
        if user_id:
            user_id = user_id[0]
        else:
            await ctx.send("Invalid user ID was provided:", user_detail)
            return

        member = self.server.get_member(int(user_id))
        if not member:
            await ctx.send("No such member found")
            return

        if member.guild_permissions.manage_messages:
            await ctx.send(
                "You cannot kick this user", delete_after=15
            )
            return

        embed = self.build_mod_action_embed(ctx, member, reason, f"You've Been Kicked")
        successfully_dmd = await self.send_dm(
            member,
            embed,
            description="You've been kicked from the Beginner.py server.\n",
        )
        if not successfully_dmd:
            reason += "\n*Unable to DM user*"

        await self.server.kick(member, reason=reason)

        await ctx.send(f"{member.display_name} has been kicked")
        await self.log_action("Kick", member, ctx.author, reason, ctx.message)
        self.save_action(
            "KICK", member, ctx.author, message=reason, reference=ctx.message.id
        )

    @Cog.command(name="purge")
    @commands.has_guild_permissions(manage_messages=True)
    async def purge(self, ctx, messages: str):
        if messages.startswith("<"):
            user_id = re.findall("\d+", messages)
            if user_id:
                member = self.server.get_member(int(user_id[0]))
                if member and member.guild_permissions.manage_messages:
                    await ctx.send(
                        "You cannot delete messages from this user", delete_after=15
                    )
                    return
                deleted = await self.purge_by_user_id(ctx, int(user_id[0]))
            else:
                await ctx.send("Invalid user ID was provided:", messages)
                return
        else:
            deleted = await self.purge_by_message_count(ctx, int(messages))

        await self.log_action(
            "Purge",
            None,
            ctx.author,
            f"Purged {deleted} messages in {ctx.message.channel.mention}",
            ctx.message,
        )

    async def purge_by_user_id(self, ctx, user_id):
        messages = await ctx.message.channel.purge(
            check=lambda message: message.author.id == user_id
        )
        await ctx.send(
            f"Deleted {len(messages)} messages sent by that user in this channel",
            delete_after=15,
        )
        return len(messages)

    async def purge_by_message_count(self, ctx, count):
        messages = await ctx.message.channel.purge(limit=min(100, count + 1))
        await ctx.send(
            f"Deleted {len(messages)} messages in this channel", delete_after=15
        )
        return len(messages)

    @Cog.command(name="mute")
    async def mute(self, ctx, user, duration, *, reason: str):
        if not (
            set(ctx.author.roles) & {self.get_role("jedi council"), self.get_role("mods")}
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
        self.save_action(
            "MUTE", member, ctx.author, message=reason, reference=message.id
        )

    @Cog.command(name="unmute")
    async def unmute(self, ctx, user):
        if not (
            set(ctx.author.roles) & {self.get_role("jedi council"), self.get_role("mods")}
        ):
            return

        member: Member = self.server.get_member(int(user[3:-1]))
        await member.remove_roles(self.get_role("muted"), reason="Mod unmute")

        await ctx.send(f"*{member.mention} is unmuted*")
        self.save_action("UNMUTE", member, ctx.author, message="Mod unmute")

    @Cog.command(name="warn")
    async def warn(self, ctx, user, *, reason: str):
        if not (
            set(ctx.author.roles) & {self.get_role("jedi council"), self.get_role("mods")}
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
        self.save_action(
            "WARN", member, ctx.author, message=reason, reference=message.id
        )

    @Cog.command()
    @commands.has_guild_permissions(manage_messages=True)
    async def history(self, ctx, member: User):
        history = list(
            ModAction.select()
            .limit(50)
            .order_by(ModAction.datetime.desc())
            .where(ModAction.user_id == member.id)
        )
        message = f"{member.mention} has no mod action history."
        if len(history):
            action_items = []
            for action in history:
                details = pickle.loads(action.details.encode())
                msg = details.get("message", "*No message*")
                action_items.append(
                    f"**{action.action_type:6} {action.datetime:%d/%m/%Y}**\n{msg}"
                )
            message = "\n".join(action_items)

        await ctx.send(
            embed=Embed(description=message, color=0xFFE873).set_author(
                name="Mod Action History"
            )
        )

    async def send_dm(
        self,
        member: Member,
        embed: Embed,
        message: Message = None,
        description: str = "",
    ):
        embed.description = f"{description}\n\n" f"Reason: {embed.description}\n\n"
        if message:
            embed.description += f"[Jump To Conversation]({message.jump_url})"

        try:
            await member.send(embed=embed)
            return True
        except discord.errors.Forbidden:
            return False

    def save_action(self, action_type: str, user: Member, mod: Member, **details):
        action = ModAction(
            action_type=action_type,
            user_id=user.id,
            mod_id=mod.id,
            datetime=datetime.utcnow(),
            details=pickle.dumps(details, 0),
        )
        action.save()

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
        await self.get_channel(
            self.settings.get("MOD_ACTION_LOG_CHANNEL", "mod-action-log")
        ).send(
            embed=Embed(
                description=f"Moderator: {mod.mention}\n"
                + (f"User: {user.mention}\n" if user else "")
                + f"Reason: {reason}"
                + ("\n" if additional_fields else "")
                + f"{additional_fields}\n\n"
                f"[Jump To Action]({message.jump_url})",
                color=0xCC2222,
            ).set_author(
                name=f"{action} @{user.display_name if user else mod.display_name}",
                icon_url=self.server.icon_url,
            )
        )

    def build_mod_action_embed(
        self, ctx, user: Member, reason: str, title: str
    ) -> Embed:
        embed = Embed(description=reason, color=0xCC2222)
        self.get_rule_for_reason(reason, embed)
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
