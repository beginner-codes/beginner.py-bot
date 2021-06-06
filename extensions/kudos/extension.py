import re
from datetime import datetime, timedelta
from discord import (
    Embed,
    Guild,
    Message,
    MessageType,
    RawReactionActionEvent,
    TextChannel,
    errors,
)
from extensions.kudos.manager import KudosManager
from extensions.help_channels.channel_manager import ChannelManager
from itertools import islice
import dippy


FIRST_TIME_BONUS = 32
DAILY_MESSAGE_BONUS = 4
WEEKLY_STREAK_BONUS = 16


class KudosExtension(dippy.Extension):
    client: dippy.Client
    log: dippy.logging.Logging
    manager: KudosManager
    help_channels: ChannelManager

    @dippy.Extension.command("!kudos help")
    async def kudos_help(self, message: Message):
        emoji = await self.manager.get_kudos_emoji(message.guild)
        emoji_list = "\n".join(
            f"- {self.manager.get_emoji(message.guild, emoji)} {points} kudos"
            for emoji, points in sorted(
                emoji.items(), key=lambda item: item[1], reverse=True
            )
        )
        await message.channel.send(
            embed=Embed(
                title="Kudos Help",
                description=(
                    f"To help everyone show appreciation we have a simple *kudos* system."
                ),
                color=0x4285F4,
            )
            .add_field(
                name="Giving Kudos",
                value=(
                    f"You can give others whenever they're helpful or do something cool. You can do this simply by "
                    f"reacting to their message with these emoji:\n{emoji_list}"
                ),
                inline=False,
            )
            .add_field(
                name="Kudos Achievements",
                value=(
                    "You can unlock achievements the more kudos you earn. Your lifetime kudos received will be used to "
                    "unlock achievements, so giving kudos to others will not slow you down.\n\n"
                    + "\n".join(
                        f"**{achievement.emoji} {achievement.name} {achievement.emoji}**\n*{achievement.kudos} Kudos "
                        f"to unlock*\n{achievement.description}\n"
                        for achievement in self.manager.achievements.values()
                    )
                ),
                inline=False,
            )
            .add_field(
                name="Daily Streaks",
                value=(
                    "You can also earn 4 kudos for your first message in the server each day, and 32 for "
                    "every 7th day in your streak. The next day is considered to be 23.5hrs after the previous time "
                    "that you received a daily kudos bonus. To maintain a streak your next message must come within 48"
                    "hours of the last daily kudos bonus."
                ),
                inline=False,
            )
            .set_thumbnail(url=self.manager.get_emoji(self.client, "expert").url)
            .set_footer(text="!kudos | !kudos help")
        )

    @dippy.Extension.command("!kudos")
    async def get_kudos_stats(self, message: Message):
        if "help" in message.content.casefold():
            return

        leaders = await self.manager.get_leaderboard(message.guild)
        user_kudos = leaders.get(message.author)
        lifetime_kudos = await self.manager.get_lifetime_kudos(message.author)

        leaderboard = []
        for index, (member, member_kudos) in islice(
            enumerate(leaders.items(), start=1), 0, 5
        ):
            name = member.display_name if member else "*Old Member*"
            entry = f"{index}. {name} has {member_kudos} kudos"
            if member == message.author:
                entry = f"**{entry}**"
            leaderboard.append(entry)

        current_streak, best_streak = await self.manager.get_streaks(message.author)
        last_active = await self.manager.get_last_active_date(message.author)
        next_day = last_active + timedelta(hours=23, minutes=30)

        plural = lambda num: "s" * (num != 1)

        streak = (
            f"Your current activity streak is {current_streak} day{plural(current_streak)}, and your best ever streak "
            f"is {best_streak} day{plural(best_streak)}."
        )
        if current_streak == best_streak:
            streak = f"Your current and best ever streak is {current_streak} day{plural(current_streak)}!!!"

        thats_in = next_day - datetime.utcnow()
        thats_in_msg = f"{thats_in.total_seconds()} seconds"
        if thats_in > timedelta(hours=1):
            thats_in_msg = f"{thats_in // timedelta(hours=1)} hours"
        elif thats_in > timedelta(minutes=1):
            thats_in_msg = f"{thats_in // timedelta(minutes=1)} minutes"

        streak = (
            f"{streak}\n*To maintain your streak be sure to send a message sometime around "
            f"{next_day.strftime('%b %-d @ %-I:%M%p')} UTC. That's in {thats_in_msg}.*"
        )

        embed = (
            Embed(
                color=0x4285F4,
                description=(
                    f"{message.author.mention} you have {user_kudos if user_kudos > 0 else 'no'} kudos left\n"
                    f"You have received {lifetime_kudos} total kudos"
                ),
                title="Kudos Stats",
            )
            .set_thumbnail(
                url="https://cdn.discordapp.com/emojis/669941420454576131.png?v=1"
            )
            .add_field(
                name="Activity Streak",
                value=streak,
                inline=False,
            )
            .set_footer(text="!kudos | !kudos help")
        )

        achievements = await self.manager.get_achievements(message.author)
        if achievements:
            embed.add_field(
                name="Achievements",
                value="\n\n".join(
                    f"**{achievement.emoji} {achievement.name} {achievement.emoji}**\n{achievement.unlock_description}"
                    for achievement in achievements
                ),
            )

        embed.add_field(name="Leader Board", value="\n".join(leaderboard), inline=False)
        await message.channel.send(embed=embed)

    @dippy.Extension.command("!import kudos")
    async def import_kudos(self, message: Message):
        if not message.author.guild_permissions.manage_channels:
            return

        for line in (await message.attachments[0].read()).strip().split(b"\n"):
            try:
                member_id, points = map(int, line.split(b","))
            except ValueError:
                print("FAILED", line)
            else:
                member = message.guild.get_member(member_id)
                if not member:
                    try:
                        member = await message.guild.fetch_member(member_id)
                    except errors.NotFound:
                        await message.channel.send(
                            f"{member_id} is no longer a member, they had {points} kudos"
                        )
                        continue
                await self.manager.set_kudos(member, points)
                await message.channel.send(
                    f"{member.display_name} now has {points} kudos"
                )

    @dippy.Extension.command("!set kudos ledger")
    async def set_kudos_ledger_channel(self, message: Message):
        if not message.author.guild_permissions.manage_channels:
            return

        channel_id, *_ = re.match(r".+?<#(\d+)>", message.content).groups()
        channel = self.client.get_channel(int(channel_id))
        await self.manager.set_ledger_channel(channel)
        await channel.send("This is now the Kudos Ledger!")

    @dippy.Extension.command("!set kudos emoji")
    async def set_kudos_emoji(self, message: Message):
        if not message.author.guild_permissions.manage_channels:
            return

        emoji = {
            name: int(value)
            for name, value in re.findall(
                r"(?:<:)?(\S+?)(?::\d+>)? (\d+)", message.content
            )
        }
        await self.manager.set_kudos_emoji(message.guild, emoji)
        await message.channel.send(
            f"Set kudos emoji\n{self._build_emoji(message.guild, emoji)}"
        )

    @dippy.Extension.command("!get kudos emoji")
    async def get_kudos_emoji(self, message: Message):
        emoji = await self.manager.get_kudos_emoji(message.guild)
        if emoji:
            await message.channel.send(self._build_emoji(message.guild, emoji))
        else:
            await message.channel.send("*No kudos emoji are set*")

    @dippy.Extension.listener("raw_reaction_add")
    async def on_reaction(self, payload: RawReactionActionEvent):
        if payload.member.bot:
            return

        channel: TextChannel = self.client.get_channel(payload.channel_id)
        emoji = await self.manager.get_kudos_emoji(channel.guild)
        if not emoji:
            return

        if payload.emoji.name not in emoji:
            return

        archive_category = (await self.help_channels.get_categories(channel.guild)).get(
            "help-archive"
        )
        if (
            not channel.permissions_for(payload.member).send_messages
            and channel.category.id != archive_category
        ):
            return

        message = await channel.fetch_message(payload.message_id)
        if message.author.bot or message.author == payload.member:
            return

        kudos = await self.manager.get_kudos(payload.member)
        giving = emoji[payload.emoji.name]
        if giving > kudos:
            await channel.send(
                f"{payload.member.mention} you can't give {giving} kudos, you only have {kudos}",
                delete_after=15,
            )
            return

        achievements = await self.manager.get_achievements(message.author)

        await self.manager.give_kudos(
            message.author,
            giving,
            f"{payload.member.mention} gave {message.author.mention} kudos",
        )
        await self.manager.take_kudos(payload.member, giving)
        await channel.send(
            f"{payload.member.mention} you gave {message.author.display_name} {giving} kudos, you have {kudos - giving}"
            f" left to give.",
            reference=message,
            mention_author=False,
            delete_after=60,
        )

        achievements = {
            achievement
            for achievement in await self.manager.get_achievements(message.author)
            if achievement not in achievements
        }
        if achievements:
            achievement_message = ", ".join(
                f"{achievement.emoji} {achievement.name} {achievement.emoji}"
                for achievement in achievements
            )
            await channel.send(
                f"{message.author.display_name} you have unlocked {achievement_message}",
                delete_after=60,
            )

    @dippy.Extension.listener("message")
    async def award_challenge_kudos(self, message: Message):
        if message.channel.id != 711930226216796170:
            return

        if not message.content.startswith("**Challenge"):
            return

        for member in message.mentions:
            await self.manager.give_kudos(
                member, 4, f"{member.mention} did the weekday challenge!!!"
            )
        await message.channel.send(
            f"Gave all {len(message.mentions)} people who did the challenge 4 kudos!!!"
        )

    @dippy.Extension.listener("message")
    async def on_message(self, message: Message):
        if (
            message.author.bot
            or not isinstance(message.channel, TextChannel)
            or message.type == MessageType.new_member
        ):
            return

        last_active_date = await self.manager.get_last_active_date(message.author)
        current_date = datetime.utcnow()
        if (
            last_active_date
            and timedelta(hours=23, minutes=30) >= current_date - last_active_date
        ):
            return

        await self.manager.set_last_active_date(message.author)
        current_streak, best_streak = await self.manager.get_streaks(message.author)

        kudos = DAILY_MESSAGE_BONUS
        reason = f"{message.author.mention} has sent their first message of the day!"
        notification = (
            f"Gave {message.author} their daily {kudos} kudos bonus! Their current activity streak is "
            f"{current_streak + 1} day{'s' * (current_streak > 0)}!"
        )
        if best_streak == 0:
            kudos = FIRST_TIME_BONUS
            reason = f"{message.author.mention} has joined the server!!!"
            await self.manager.set_streak(message.author, 1)

            notification = f"Gave {message.author} {kudos} kudos for joining us!!!"

        elif last_active_date - current_date < timedelta(days=2):
            current_streak += 1
            await self.manager.set_streak(message.author, current_streak)

            if current_streak % 7 == 0:
                kudos = WEEKLY_STREAK_BONUS
                weeks = current_streak // 7
                reason = f"{message.author.mention} has messaged every day for {weeks} week{'s' * (weeks > 1)}!"

                notification = (
                    f"Gave {message.author} {kudos} for their 7 day activity streak!!!"
                )
        else:
            await self.manager.set_streak(message.author, 1)

        await self.manager.give_kudos(message.author, kudos, reason)
        await message.channel.send(notification, delete_after=60)

    def _build_emoji(self, guild: Guild, emoji: dict[str, int]) -> str:
        return "\n".join(
            f"{self.manager.get_emoji(guild, name)} {value}"
            for name, value in sorted(emoji.items(), key=lambda item: item[1])
        )
