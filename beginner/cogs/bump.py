from beginner.cog import Cog
from beginner.colors import *
from beginner.models.points import Points
from beginner.scheduler import schedule, task_scheduled
from beginner.tags import tag
from datetime import datetime, timedelta
import asyncio
import discord
import discord.ext.commands
import os
import peewee
import requests
import re
import bs4


class Bumping(Cog):
    def __init__(self, client):
        super().__init__(client)
        self._channel = None
        self._disboard = None
        self._role = None
        self._bump_lock = asyncio.Lock()
        self._bump_score_days = 7

    @property
    def channel(self) -> discord.TextChannel:
        if not self._channel:
            self._channel = self.get_channel(os.environ.get("BUMP_CHANNEL", "👊bumping"))
        return self._channel

    @property
    def disboard(self) -> discord.Member:
        if not self._disboard:
            self._disboard = self.server.get_member(302050872383242240)
        return self._disboard

    @property
    def role(self) -> discord.Role:
        if not self._role:
            self._role = self.get_role("bumpers")
        return self._role

    @Cog.command(name="d", aliases=["D"])
    async def bump_handler(self, ctx: discord.ext.commands.Context, action: str):
        if not action.casefold() == "bump":
            return

        await ctx.send(f"{ctx.author.display_name} bumped", delete_after=10)

        async with self._bump_lock:
            if task_scheduled("bump-reminder"):
                await ctx.send(
                    embed=discord.Embed(
                        color=YELLOW,
                        description=f"{ctx.author.mention} please wait until the next bump reminder",
                        title="Please Wait"
                    ),
                    delete_after=20
                )
                return

            if not self.disboard.status == discord.Status.online:
                await ctx.send(
                    embed=(
                        discord.Embed(
                            color=RED,
                            description=(
                                f"{ctx.author.mention} bump failed, {self.disboard.mention} appears to be offline. "
                                "I'll check once a minute and let you know when it comes back online"
                            ),
                            title="Bump Failed - Offline"
                        )
                        .set_thumbnail(url="https://cdn.discordapp.com/emojis/651959497698574338.png?v=1")
                    )
                )
                await self.bump_recovery()
                return

            async with ctx.channel.typing():
                await ctx.send("Watching for the bump confirmation...", delete_after=30)

                await asyncio.sleep(30)
                next_bump_timer = await self.get_next_bump_timer()

                next_bump = timedelta(seconds=next_bump_timer)
                if next_bump_timer >= 0:
                    schedule("bump-reminder", next_bump, self.bump_reminder)
                await self.clear_channel()

                message = f"Successfully bumped!"
                thumbnail = "https://cdn.discordapp.com/emojis/711749954837807135.png?v=1"
                if next_bump.seconds <= 7000:
                    message = f"Server was already bumped. {ctx.author.mention} try again at the next bump reminder."
                title = f"Thanks {ctx.author.display_name}!" if next_bump.seconds > 7000 else "Already Bumped"
                color = BLUE if next_bump.seconds > 7000 else YELLOW

                if next_bump_timer == -1:
                    message = f"Bump did not go through. Try again in a little while."
                    title = f"Bump Did Not Go Through"
                    color = YELLOW
                    thumbnail = "https://cdn.discordapp.com/emojis/651959497698574338.png?v=1"


                next_bump_message = []
                next_bump_hour = next_bump.seconds//3600
                next_bump_minutes = next_bump.seconds // 60 % 60
                if next_bump_hour > 0:
                    next_bump_message.append(f"{next_bump_hour} hour{'s' if next_bump_hour > 1 else ''}")
                if next_bump_minutes > 0:
                    next_bump_message.append(f"{next_bump_minutes} minute{'s' if next_bump_minutes > 1 else ''}")

                await ctx.send(
                    embed=(
                        discord.Embed(
                            color=color,
                            description=f"{message} Next bump in {' & '.join(next_bump_message)}",
                            title=title
                        )
                        .set_thumbnail(url=thumbnail)
                    )
                )

                if next_bump.seconds > 7000:
                    await self.award_points(ctx.message)

    @Cog.listener()
    async def on_message(self, message: discord.Message):
        if not message.channel.id == self.channel.id:
            return

        if message.author.id == self.client.user.id:
            return

        if message.author.bot:
            return

        await message.delete()

    async def award_points(self, message: discord.Message):
        king_id = self.get_bump_king_id()
        self.award_bump_points(message.author.id)

        new_king_id = self.get_bump_king_id()
        if new_king_id != king_id:
            role = self.get_role("bump king")

            if king_id:
                await self.server.get_member(king_id).remove_roles(role)

            new_king = self.server.get_member(new_king_id)
            await new_king.add_roles(role)

            channel = self.get_channel(os.environ.get("BUMP_KING_ANNOUNCE_CHANNEL", "general"))
            await channel.send(
                embed=discord.Embed(
                    description=f"All hail {new_king.mention} our new {role.mention}!!!"
                ).set_author(name="New Bump King", icon_url=self.server.icon_url)
            )

    def award_bump_points(self, author_id):
        bump = Points(
            awarded=datetime.utcnow(),
            user_id=author_id,
            points=1,
            point_type="BUMP"
        )
        bump.save()

    def get_bump_king_id(self):
        scores = (
            Points.select(Points.user_id, peewee.fn.sum(Points.points))
            .order_by(peewee.fn.sum(Points.points).desc())
            .group_by(Points.user_id)
            .filter(
                Points.point_type == "BUMP",
                Points.awarded > datetime.utcnow() - timedelta(days=self._bump_score_days)
            )
            .limit(1)
        )
        return scores.scalar() if scores.count() else None

    @Cog.command()
    async def bump_leaderboard(self, ctx):
        scores = list(
            Points.select(Points.user_id, peewee.fn.sum(Points.points))
                .order_by(peewee.fn.sum(Points.points).desc())
                .group_by(Points.user_id)
                .filter(
                    Points.point_type == "BUMP",
                    Points.awarded > datetime.utcnow() - timedelta(days=self._bump_score_days)
                )
                .limit(5)
        )
        if scores:
            king = scores.pop(0)
            embed = discord.Embed(
                title="Bump Leaders",
                description=f"Here are the people who have bumped the most in the last {self._bump_score_days} days!",
                color=YELLOW
            ).add_field(
                name="👑 Bump King 👑",
                value=f"{ctx.guild.get_member(king.user_id).mention} is our Bump King with {king.sum} bumps!",
                inline=False
            )
            if scores:
                embed.add_field(
                    name="Runners Up",
                    value="\n".join(
                        f"- {ctx.guild.get_member(bumper.user_id).mention} has bumped {bumper.sum} times"
                        for bumper in scores
                    ),
                    inline=False
                )
            await ctx.send(embed=embed)
        else:
            await ctx.send("No bumpers found")

    @tag("schedule", "disboard-bump-reminder")
    async def bump_reminder(self):
        self.logger.debug(f"SENDING BUMP REMINDER: {self.role.name}")
        await self.clear_channel()
        if self.disboard.status == discord.Status.online:
            await self.channel.send(
                f"{self.role.mention} It's been 2hrs since the last bump!\n"
                f"*Use the command `!d bump` now!*"
            )
        else:
            await self.channel.send(
                embed=discord.Embed(
                    color=RED,
                    description=(
                        f"Whoa {self.disboard.mention} appears to be offline right now! "
                        "I'll check once a minute and let you know when it comes back online"
                    )
                )
            )
            await self.bump_recovery()

    @tag("schedule", "disboard-bump-recovery")
    async def bump_recovery(self):
        if self.disboard.status == discord.Status.online:
            await self.bump_reminder()
            return

        schedule("disboard-recovery", timedelta(minutes=1), self.bump_recovery, no_duplication=True)

    async def clear_channel(self):
        explanation = await self.get_explanation_message()
        await self.channel.purge(check=lambda m: m.author.id == self.client.user.id and not m.id == explanation.id)

    async def get_next_bump_timer(self):
        history = self.channel.history(limit=100)
        async for message in history:
            if message.author == self.disboard:
                content = message.embeds[0].description
                if ":thumbsup:" in content:
                    return 60 * 120 - (datetime.utcnow() - message.created_at).seconds
                else:
                    try:
                        end_index = content.find(" minutes")
                        start_index = content[:end_index].rfind(" ") + 1
                        minutes = int(content[start_index:end_index])
                        return minutes * 60
                    except ValueError:
                        pass  # Something blew up, wrong type of message, so do nothing

        return -1

    @Cog.listener()
    async def on_raw_reaction_add(self, reaction):
        if reaction.emoji.name != "🔔":
            return

        if reaction.message_id != (await self.get_explanation_message()).id:
            return

        member = self.server.get_member(reaction.user_id)
        if member.bot:
            return

        if self.role not in member.roles:
            await self.add_bumper_role(member)

    @Cog.listener()
    async def on_raw_reaction_remove(self, reaction):
        if reaction.emoji.name != "🔔":
            return

        if reaction.message_id != (await self.get_explanation_message()).id:
            return

        member = self.server.get_member(reaction.user_id)
        if member.bot:
            return

        if self.role in member.roles:
            await self.remove_bumper_role(member)

    async def add_bumper_role(self, member):
        await member.add_roles(self.role)
        await self.channel.send(
            f"{member.mention} you will be tagged by bump reminders", delete_after=10
        )

    async def create_explanation_message(self):
        message = await self.channel.send(
            embed=discord.Embed(
                description=(
                    f"To help us stay at the top of Disboard join the *Bump Squad* by reacting with the 🔔, "
                    f"react again to leave the squad"
                ),
                color=0x306998,
            ).set_author(name="Beginner.py Bump Squad", icon_url=self.server.icon_url)
        )
        await message.add_reaction("🔔")
        return message

    async def get_explanation_message(self):
        messages = await self.channel.history(oldest_first=True, limit=1).flatten()
        if len(messages) == 0:
            return await self.create_explanation_message()
        return messages[0]

    async def remove_bumper_role(self, member):
        await member.remove_roles(self.role)
        await self.channel.send(
            f"{member.mention} you will no longer be tagged by bump reminders",
            delete_after=10,
        )


def setup(client):
    client.add_cog(Bumping(client))
