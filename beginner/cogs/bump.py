from beginner.cog import Cog, commands
from beginner.colors import *
from beginner.models.points import Points
from beginner.scheduler import schedule, task_scheduled
from beginner.tags import tag
from datetime import datetime, timedelta
import asyncio
import nextcord
import nextcord.ext.commands
import os
import peewee
import pytz


class BumpButton(nextcord.ui.View):
    @nextcord.ui.button(
        emoji="🔔", style=nextcord.ButtonStyle.blurple, custom_id="BumpButton"
    )
    async def button_pressed(self, _, interaction: nextcord.Interaction):
        guild = interaction.guild
        bump_role = nextcord.utils.get(guild.roles, name="Bumpers")
        if bump_role in interaction.user.roles:
            await interaction.user.remove_roles(bump_role)
            await interaction.response.send_message(
                f"{interaction.user.mention} you will no longer be tagged by bump reminders"
            )
            await asyncio.sleep(7)
            await interaction.delete_original_message()
        elif bump_role not in interaction.user.roles:
            await interaction.user.add_roles(bump_role)
            await interaction.response.send_message(
                f"{interaction.user.mention} you will be tagged by bump reminders"
            )
            await asyncio.sleep(7)
            await interaction.delete_original_message()


class Bumping(Cog):
    def __init__(self, client):
        super().__init__(client)
        self.bump_button_added = False
        self._channel = None
        self._disboard = None
        self._role = None
        self._bump_lock = asyncio.Lock()
        self._bump_score_days = 7
        self._message_queue = asyncio.Queue()

    def log_bump(self, message: str, bumper: nextcord.Member):
        loop = asyncio.get_event_loop()
        loop.create_task(
            self.get_channel("bump-log").send(
                f"{datetime.utcnow().isoformat()}: {bumper.display_name}\n> {message}"
            )
        )

    @property
    def channel(self) -> nextcord.TextChannel:
        if not self._channel:
            self._channel = self.get_channel(os.environ.get("BUMP_CHANNEL", "👊bumping"))
        return self._channel

    @property
    def disboard(self) -> nextcord.Member:
        if not self._disboard:
            self._disboard = self.server.get_member(302050872383242240)
        return self._disboard

    @property
    def role(self) -> nextcord.Role:
        if not self._role:
            self._role = self.get_role("bumpers")
        return self._role

    @commands.Cog.listener()
    async def on_ready(self):
        if not self.bump_button_added:
            self.client.add_view(BumpButton(timeout=None))
            self.bump_button_added = True

    @Cog.command()
    async def bumpers(self, ctx):
        scores = (
            Points.select(Points.user_id, peewee.fn.sum(Points.points))
            .order_by(peewee.fn.sum(Points.points).desc())
            .group_by(Points.user_id)
            .filter(
                Points.point_type == "BUMP",
                Points.awarded
                > datetime.utcnow() - timedelta(days=self._bump_score_days),
            )
            .limit(30)
            .tuples()
        )
        message = []
        for emoji, (user_id, points) in zip(
            ["🥇", "🥈", "🥉"] + ["✨"] * max(len(scores) - 3, 0), scores
        ):
            member: nextcord.Member = self.server.get_member(user_id)
            message.append(
                f"{emoji} {member.mention if member else '*Unknown*'} **{str(points)}**"
            )

        await ctx.send(
            embed=nextcord.Embed(
                title="🏆 Bumping Leaderboard 🏆",
                description="\n".join(message),
                color=YELLOW,
            )
        )

    @Cog.command()
    async def bumps(self, ctx):
        bumps = (
            Points.select(Points.user_id, Points.awarded)
            .order_by(Points.awarded.desc())
            .filter(
                Points.point_type == "BUMP",
                Points.awarded
                > datetime.utcnow() - timedelta(days=self._bump_score_days),
            )
            .tuples()
        )
        message = ["**Most Recent**"]
        now = datetime.utcnow()
        days = 0
        for index, (user_id, awarded) in enumerate(bumps, start=1):
            if (now - awarded) // timedelta(days=1) > days:
                days = (now - awarded) // timedelta(days=1)
                message.append(f"\n**{days * 24} Hours Ago**")
            message.append(
                f"{index}. <t:{awarded.timestamp():.0f}:t> {ctx.guild.get_member(user_id) or '*Unknown User*'}"
            )
        await ctx.send(
            embed=nextcord.Embed(
                title="👊 Bump List 🕰",
                description="\n".join(message),
                color=YELLOW,
            )
        )

    @Cog.command(name="d", aliases=["D"])
    async def bump_handler(self, ctx: nextcord.ext.commands.Context, action: str):
        if not action.casefold() == "bump":
            return

        await ctx.send(f"🟢 {ctx.author.display_name} bumped", delete_after=10)
        self.log_bump(f"Bumped", ctx.author)

        async with self._bump_lock:
            if task_scheduled("disboard-bump-reminder"):
                await ctx.send(
                    embed=nextcord.Embed(
                        color=YELLOW,
                        description=f"{ctx.author.mention} please wait until the next bump reminder",
                        title="Please Wait",
                    ),
                    delete_after=20,
                )
                self.log_bump(f"Bump already scheduled", ctx.author)
                return

            if not self.disboard.status == nextcord.Status.online:
                await ctx.send(
                    embed=(
                        nextcord.Embed(
                            color=RED,
                            description=(
                                f"Whoa {self.disboard.mention} appears to be offline right now! "
                                "I'll monitor the bump bot's status and notify everyone when it comes back online."
                            ),
                            title="Bump Failed - Offline",
                        ).set_thumbnail(
                            url="https://cdn.discordapp.com/emojis/651959497698574338.png?v=1"
                        )
                    )
                )
                self.log_bump("Bot is not online", ctx.author)
                return

            async with ctx.channel.typing():
                self.log_bump("Waiting for bump reminder", ctx.author)
                await ctx.send("Watching for the bump confirmation...", delete_after=30)

                next_bump_timer = await self.get_next_bump_timer()

                next_bump = (
                    timedelta(seconds=next_bump_timer)
                    if next_bump_timer > 0
                    else timedelta(hours=2)
                )
                self.log_bump(
                    f"Reminder set to go off in {':'.join(map(str, divmod(next_bump.total_seconds(), 60)))} (m:s)",
                    ctx.author,
                )
                schedule("disboard-bump-reminder", next_bump, self.bump_reminder)
                await self.clear_channel()

                message = f"Successfully bumped!"
                thumbnail = (
                    "https://cdn.discordapp.com/emojis/711749954837807135.png?v=1"
                )
                if next_bump.total_seconds() <= 7000:
                    self.log_bump(
                        f"Server already bumped {next_bump.total_seconds()} <= 7000",
                        ctx.author,
                    )
                    message = f"Server was already bumped. {ctx.author.mention} try again at the next bump reminder."
                title = (
                    f"Thanks {ctx.author.display_name}!"
                    if next_bump.total_seconds() > 7000
                    else "Already Bumped"
                )
                color = BLUE if next_bump.total_seconds() > 7000 else YELLOW

                if next_bump_timer == -1:
                    self.log_bump("Bump didn't go through", ctx.author)
                    message = f"Bump did not go through. Try again in a little while."
                    title = f"Bump Did Not Go Through"
                    color = YELLOW
                    thumbnail = (
                        "https://cdn.discordapp.com/emojis/651959497698574338.png?v=1"
                    )

                next_bump_message = []
                next_bump_hour = int(next_bump.total_seconds() // 3600)
                next_bump_minutes = int(next_bump.total_seconds() // 60 % 60)
                if next_bump_hour > 0:
                    next_bump_message.append(
                        f"{next_bump_hour} hour{'s' if next_bump_hour > 1 else ''}"
                    )
                if next_bump_minutes > 0:
                    next_bump_message.append(
                        f"{next_bump_minutes} minute{'s' if next_bump_minutes > 1 else ''}"
                    )

                await ctx.send(
                    embed=(
                        nextcord.Embed(
                            color=color,
                            description=f"{message} Next bump in {' & '.join(next_bump_message)}",
                            title=title,
                            timestamp=datetime.utcnow() + next_bump,
                        )
                        .set_thumbnail(url=thumbnail)
                        .set_footer(text="Next bump")
                    )
                )
                self.log_bump(f"Next bump in {':'.join(next_bump_message)}", ctx.author)

                if next_bump.total_seconds() > 7000:
                    self.log_bump("Gave bump points", ctx.author)
                    await self.award_points(ctx.message)

    @Cog.listener()
    async def on_member_update(self, before: nextcord.Member, after: nextcord.Member):
        if before != self.disboard:
            return

        if before.status == after.status:
            return

        if task_scheduled("disboard-bump-reminder"):
            return

        if after.status.online == nextcord.Status.online:
            await self.bump_reminder()

    @Cog.listener()
    async def on_message(self, message: nextcord.Message):
        if not message.channel.id == self.channel.id:
            return

        if message.author.id == self.client.user.id:
            return

        if message.author == self.disboard:
            self.log_bump("Queued message", message.author)
            await self._message_queue.put(message)

        if message.author.bot:
            return

        self.log_bump("Deleted message", message.author)
        await message.delete()

    async def award_points(self, message: nextcord.Message):
        self.award_bump_points(message.author.id)

        king_id = self.get_bump_king_id()
        king = self.server.get_member(king_id)
        role: nextcord.Role = self.get_role("bump king")
        if role not in king.roles:
            self.log_bump("New king", king)

            for member in role.members:
                await member.remove_roles(role)

            await king.add_roles(role)
            await self.announce_king()

    @Cog.command()
    @commands.has_guild_permissions(manage_channels=True)
    async def send_explanation_message(self, _):
        await self.create_explanation_message()

    @Cog.command(name="announce_king")
    @commands.has_guild_permissions(manage_channels=True)
    async def command_announce_king(self, _):
        await self.announce_king()

    async def announce_king(self):
        king_id = self.get_bump_king_id()
        king = self.server.get_member(king_id)
        role = self.get_role("bump king")
        channel = self.get_channel(
            os.environ.get("BUMP_KING_ANNOUNCE_CHANNEL", "🦄off-topic")
        )
        await channel.send(
            embed=nextcord.Embed(
                description=f"All hail {king.mention} our new {role.mention}!!!"
            ).set_author(name="New Bump King", icon_url=self.server.icon.url)
        )

    def award_bump_points(self, author_id):
        bump = Points(
            awarded=datetime.utcnow(), user_id=author_id, points=1, point_type="BUMP"
        )
        bump.save()

    def get_bump_king_id(self):
        scores = (
            Points.select(Points.user_id, peewee.fn.sum(Points.points))
            .order_by(peewee.fn.sum(Points.points).desc())
            .group_by(Points.user_id)
            .filter(
                Points.point_type == "BUMP",
                Points.awarded
                > datetime.utcnow() - timedelta(days=self._bump_score_days),
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
                Points.awarded
                > datetime.utcnow() - timedelta(days=self._bump_score_days),
            )
            .limit(5)
        )
        if scores:
            king = scores.pop(0)
            embed = nextcord.Embed(
                title="Bump Leaders",
                description=f"Here are the people who have bumped the most in the last {self._bump_score_days} days!",
                color=YELLOW,
            ).add_field(
                name="👑 Bump King 👑",
                value=f"{ctx.guild.get_member(king.user_id).mention} is our Bump King with {king.sum} bumps!",
                inline=False,
            )
            if scores:
                embed.add_field(
                    name="Runners Up",
                    value="\n".join(
                        f"- {ctx.guild.get_member(bumper.user_id).mention} has bumped {bumper.sum} times"
                        for bumper in scores
                    ),
                    inline=False,
                )
            await ctx.send(embed=embed)
        else:
            await ctx.send("No bumpers found")

    @tag("schedule", "disboard-bump-reminders")
    async def bump_reminder(self):
        self.logger.debug(f"SENDING BUMP REMINDER: {self.role.name}")
        await self.clear_channel()
        if self.disboard.status == nextcord.Status.online:
            self.log_bump("Sending bump reminder", self.server.me)
            await self.channel.send(
                f"{self.role.mention} It's been 2hrs since the last bump!\n"
                f"*Use the command `!d bump` now!*"
            )
        else:
            self.log_bump("Bot appears to be offline", self.server.me)
            await self.channel.send(
                embed=nextcord.Embed(
                    color=RED,
                    description=(
                        f"Whoa {self.disboard.mention} appears to be offline right now! "
                        "I'll monitor the bump bot's status and notify everyone when it comes back online."
                    ),
                )
            )

    async def clear_channel(self):
        self.log_bump("Clearing bump channel", self.server.me)
        explanation = await self.get_explanation_message()
        await self.channel.purge(check=lambda m: not m.id == explanation.id)

    async def get_next_bump_timer(self):
        started_watching = pytz.utc.localize(datetime.utcnow())
        while pytz.utc.localize(datetime.utcnow()) - started_watching <= timedelta(
            minutes=1
        ):
            try:
                self.log_bump("Looking for bump confirmation", self.server.me)
                message = await asyncio.wait_for(self._message_queue.get(), 60)
            except asyncio.TimeoutError:
                break

            created = message.created_at
            time_since_created = (
                started_watching - created
                if started_watching > created
                else timedelta()
            )
            if time_since_created >= timedelta(minutes=1):
                self.log_bump(
                    f"Message is too old {time_since_created}", self.server.me
                )
                continue

            content = message.embeds[0].description
            if ":thumbsup:" in content:
                next_reminder = int(
                    (timedelta(hours=2) - time_since_created).total_seconds()
                )
                self.log_bump(f"Next reminder in {next_reminder}", self.server.me)
                return next_reminder
            else:
                end_index = content.find(" minutes")
                start_index = content[:end_index].rfind(" ") + 1
                try:
                    minutes = int(content[start_index:end_index])
                except ValueError:
                    self.log_bump(
                        f"Failed to find duration in message\n\n> {content}",
                        self.server.me,
                    )
                else:
                    next_reminder = int(
                        (
                            timedelta(minutes=minutes) - time_since_created
                        ).total_seconds()
                    )
                    self.log_bump(
                        f"Next reminder in {next_reminder} seconds\n\n> {content}",
                        self.server.me,
                    )
                    return next_reminder

        self.log_bump("Seems no confirmation was found", self.server.me)
        return -1

    async def create_explanation_message(self):
        return await self.channel.send(
            embed=nextcord.Embed(
                title="Beginner.py Bump Squad",
                description=(
                    f"To help us stay at the top of Disboard join the *Bump Squad* by hitting the button to be notified"
                    f" when it's time to bump. Hit the button again at anytime to turn off the bump reminder "
                    f"notifications."
                ),
                color=0x306998,
            ),
            view=BumpButton(timeout=None),
        )

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
