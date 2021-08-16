from bevy import Injectable
from datetime import datetime, timedelta
from discord import (
    Embed,
    Emoji,
    Guild,
    Member,
    Message,
    PartialMessage,
    TextChannel,
    utils,
)
from extensions.kudos.achievements import Achievements, Achievement
from typing import Optional
import dippy.labels


class KudosManager(Injectable):
    achievements: Achievements
    client: dippy.Client
    labels: dippy.labels.storage.StorageInterface

    def __init__(self):
        self._achievements = []
        self._ledger_channels: dict[Guild, TextChannel] = {}
        self._kudos_emoji: dict[Guild, dict[str, int]] = {}

    def get_emoji(self, guild: Guild, name: str) -> Emoji:
        return utils.get(guild.emojis, name=name) or name

    async def get_kudos_emoji(self, guild: Guild) -> dict[str, int]:
        if guild not in self._kudos_emoji:
            self._kudos_emoji[guild] = await self.labels.get(
                "guild", guild.id, "kudos_emoji", default={}
            )
        return self._kudos_emoji[guild]

    async def set_kudos_emoji(self, guild: Guild, emoji: dict[str, int]):
        await self.labels.set("guild", guild.id, "kudos_emoji", emoji)
        self._kudos_emoji[guild] = emoji

    async def get_leaderboard(self, guild: Guild) -> dict[Member, int]:
        leaderboard = await self.labels.find(f"member[{guild.id}]", key="kudos")
        return {
            guild.get_member(label.id): label.value
            for label in sorted(
                leaderboard, key=lambda member: member.value, reverse=True
            )
        }

    async def get_lifetime_leaderboard(self, guild: Guild) -> dict[Member, int]:
        leaderboard = await self.labels.find(
            f"member[{guild.id}]", key="lifetime_kudos"
        )
        leaders = await self.get_leaderboard(guild)
        leaders.update(
            {
                guild.get_member(label.id): label.value
                for label in sorted(leaderboard, key=lambda member: member.value)
            }
        )
        return dict(sorted(leaders.items(), key=lambda item: item[1], reverse=True))

    async def award_achievement(self, member: Member, achievement_key: str) -> bool:
        achievement_keys = await self.get_achievement_keys(member)
        if achievement_key in achievement_keys:
            return False

        achievement_keys.add(achievement_key)
        await self._send_achievement_message_to_ledger(
            member.guild, self.achievements[achievement_key], member
        )
        await self.set_achievements(member, achievement_keys)

        await self.achievements.awarded_achievement(
            member, self.achievements[achievement_key]
        )
        return True

    async def _determine_achievements(self, member: Member, kudos: int):
        achievements = await self.get_achievement_keys(member)
        days = await self.get_days_active(member)
        for achievement_key, achievement in self.achievements.items():
            if achievement_key not in achievements and (
                (kudos >= achievement.kudos or achievement.kudos == -1)
                or (days >= achievement.days_active or achievement.days_active == -1)
            ):
                await self.award_achievement(member, achievement_key)

    async def get_achievements(self, member: Member) -> set[Achievement]:
        return {
            self.achievements[achievement_key]
            for achievement_key in await self.get_achievement_keys(member)
            if achievement_key in self.achievements
        }

    async def get_achievement_keys(self, member: Member) -> set[str]:
        return await self.labels.get(
            f"member[{member.guild.id}]", member.id, "achievements", set()
        )

    async def has_achievement(self, member: Member, achievement_key: str) -> bool:
        achievements = await self.get_achievement_keys(member)
        return achievement_key in achievements

    async def set_achievements(self, member: Member, achievement_keys: set[str]):
        await self.labels.set(
            f"member[{member.guild.id}]", member.id, "achievements", achievement_keys
        )

    def create_embed(self, content: str = "", title: str = "") -> Embed:
        return Embed(title=title, description=content, color=0x4285F4).set_footer(
            text="!kudos | !kudos help"
        )

    async def give_kudos(self, member: Member, amount: int, reason: str):
        kudos = await self.get_kudos(member)
        await self.set_kudos(member, kudos + amount)

        lifetime_kudos = await self.get_lifetime_kudos(member) or kudos
        await self.set_lifetime_kudos(member, lifetime_kudos + amount)

        await self._send_kudos_message_to_ledger(
            member.guild, amount, reason, member.avatar_url
        )

        await self._determine_achievements(member, kudos + amount)

    async def take_kudos(self, member: Member, amount: int):
        kudos = await self.get_kudos(member)
        await self.set_kudos(member, kudos - amount)

        # Preserve old total
        lifetime_kudos = await self.get_lifetime_kudos(member, False)
        if lifetime_kudos is None:
            await self.set_lifetime_kudos(member, kudos)

    async def get_kudos(self, member: Member) -> int:
        kudos = await self.labels.get(
            f"member[{member.guild.id}]", member.id, "kudos", default=0
        )
        emoji = await self.get_kudos_emoji(member.guild)
        helper = utils.get(member.guild.roles, name="helpers")
        return max(*emoji.values(), kudos) if helper in member.roles else kudos

    async def get_lifetime_kudos(self, member: Member, use_default: bool = True) -> int:
        kudos = await self.labels.get(
            f"member[{member.guild.id}]", member.id, "lifetime_kudos", default=None
        )
        return kudos

    async def set_kudos(self, member: Member, amount: int):
        await self.labels.set(f"member[{member.guild.id}]", member.id, "kudos", amount)

    async def set_lifetime_kudos(self, member: Member, amount: int):
        await self.labels.set(
            f"member[{member.guild.id}]", member.id, "lifetime_kudos", amount
        )

    async def get_last_active_date(self, member: Member) -> Optional[datetime]:
        date_str = await self.labels.get(
            f"member[{member.guild.id}]", member.id, "last_active_date"
        )
        return datetime.fromisoformat(date_str) if date_str else None

    async def set_last_active_date(self, member: Member):
        await self.labels.set(
            f"member[{member.guild.id}]",
            member.id,
            "last_active_date",
            datetime.utcnow().isoformat(),
        )

    async def get_streaks(self, member: Member) -> tuple[int, int]:
        return await self.labels.get(
            f"member[{member.guild.id}]",
            member.id,
            "messaging_streak",
            default=(0, 0),
        )

    async def set_streak(self, member: Member, days: int):
        best, current = await self.get_streaks(member)
        await self.labels.set(
            f"member[{member.guild.id}]",
            member.id,
            "messaging_streak",
            (days, max(best, days)),
        )

        await self.labels.set(
            f"member[{member.guild.id}]",
            member.id,
            "total-days-active",
            await self.get_days_active(member) + 1,
        )

    async def get_days_active(self, member: Member) -> int:
        return await self.labels.get(
            f"member[{member.guild.id}]", member.id, "total-days-active", default=0
        )

    async def get_recent_kudos(
        self, member: Member
    ) -> dict[Member, tuple[datetime, int]]:
        recents = {}
        now = datetime.utcnow()
        kudos_given = await self.labels.get(
            f"member[{member.guild.id}]", member.id, "recent_kudos", {}
        )
        for giver_id, (iso_date, kudos) in kudos_given.items():
            giver = member.guild.get_member(giver_id)
            date = datetime.fromisoformat(iso_date)
            if giver and (now - date) < timedelta(minutes=kudos * 7.5):
                recents[giver] = (date, kudos)

        return recents

    async def add_recent_kudos(self, member: Member, giver: Member, kudos: int):
        recents = await self.get_recent_kudos(member)
        recents[giver] = (datetime.utcnow(), kudos)

        await self.labels.set(
            f"member[{member.guild.id}]",
            member.id,
            "recent_kudos",
            {
                _giver.id: (_date.isoformat(), _kudos)
                for _giver, (_date, _kudos) in recents.items()
            },
        )

    async def get_ledger_channel(self, guild: Guild) -> Optional[TextChannel]:
        if guild not in self._ledger_channels:
            channel_id = await self.labels.get(
                "guild", guild.id, "kudos_ledger_channel"
            )
            self._ledger_channels[guild] = guild.get_channel(channel_id)

        return self._ledger_channels[guild]

    async def set_ledger_channel(self, channel: TextChannel):
        await self.labels.set(
            "guild", channel.guild.id, "kudos_ledger_channel", channel.id
        )
        self._ledger_channels[channel.guild] = channel

    async def get_kudos_reply_details(
        self, message: Message
    ) -> tuple[int, int, Optional[PartialMessage]]:
        kudos_given, num_members, message_id = await self.labels.get(
            "message", message.id, "kudos-response-message-id", (0, 0, None)
        )
        kudos_message = message_id and message.channel.get_partial_message(message_id)
        return kudos_given, num_members, kudos_message

    async def set_kudos_reply_details(
        self,
        message: Message,
        kudos_given: int,
        num_members: int,
        kudos_message: Message,
    ):
        await self.labels.set(
            "message",
            message.id,
            "kudos-response-message-id",
            (kudos_given, num_members, kudos_message.id),
        )

    async def _send_kudos_message_to_ledger(
        self, guild: Guild, kudos: int, message: str, image_url: Optional[str] = None
    ):
        action = "Gave" if kudos > 0 else "Took"
        await self._send_message_to_ledger(
            guild, message, f"{action} {abs(kudos)} kudos!!!", image_url
        )

    async def _send_achievement_message_to_ledger(
        self,
        guild: Guild,
        achievement: Achievement,
        member: Member,
        image_url: Optional[str] = None,
    ):
        await self._send_message_to_ledger(
            guild,
            f"{achievement.unlock_description}",
            f"You unlocked **{achievement.emoji} {achievement.name} {achievement.emoji}**!!!",
            image_url,
            mention=member,
        )

    async def _send_message_to_ledger(
        self,
        guild: Guild,
        message: str,
        title: str,
        image_url: Optional[str] = None,
        mention: Optional[Member] = None,
    ):
        channel = await self.get_ledger_channel(guild)
        if channel:
            embed = self.create_embed(message, title)
            if image_url:
                embed.set_thumbnail(url=image_url)
            await channel.send(content=mention.mention if mention else "", embed=embed)
