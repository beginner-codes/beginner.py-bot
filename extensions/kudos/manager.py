from bevy import Injectable
from datetime import date, datetime
from discord import Embed, Emoji, Guild, Member, Message, TextChannel, utils
from typing import Optional
import dippy.labels


class KudosManager(Injectable):
    labels: dippy.labels.storage.StorageInterface
    client: dippy.Client

    def __init__(self):
        self._ledger_channels: dict[Guild, TextChannel] = {}

    def get_emoji(self, guild: Guild, name: str) -> Emoji:
        return utils.get(guild.emojis, name=name) or name

    async def get_kudos_emoji(self, guild: Guild) -> dict[str, int]:
        return await self.labels.get("guild", guild.id, "kudos_emoji", default={})

    async def set_kudos_emoji(self, guild: Guild, emoji: dict[str, int]):
        await self.labels.set("guild", guild.id, "kudos_emoji", emoji)

    async def get_leaderboard(self, guild: Guild) -> dict[Member, int]:
        leaderboard = await self.labels.find(f"member[{guild.id}]", key="kudos")
        return {
            guild.get_member(label.id): label.value
            for label in sorted(
                leaderboard, key=lambda member: member.value, reverse=True
            )
        }

    def create_embed(self, guild: Guild, content: str = "", title: str = "") -> Embed:
        return (
            Embed(description=content, color=0x4285F4)
            .set_footer(text="!kudos | !kudos help")
            .set_author(
                icon_url=utils.get(self.client.emojis, name="expert").url, name=title
            )
        )

    async def give_kudos(self, member: Member, amount: int, reason: str):
        kudos = await self.get_kudos(member)
        await self.set_kudos(member, kudos + amount)
        lifetime_kudos = await self.get_lifetime_kudos(member)
        await self.set_lifetime_kudos(member, lifetime_kudos + amount)
        await self._send_message_to_ledger(
            member.guild, amount, reason, member.avatar_url
        )

    async def take_kudos(self, member: Member, amount: int):
        kudos = await self.get_kudos(member)
        await self.set_kudos(member, kudos - amount)

        # Preserve old total
        lifetime_kudos = await self.get_lifetime_kudos(member, False)
        if lifetime_kudos is None:
            await self.set_lifetime_kudos(member, kudos)

    async def get_kudos(self, member: Member) -> int:
        return await self.labels.get(
            f"member[{member.guild.id}]", member.id, "kudos", default=0
        )

    async def get_lifetime_kudos(self, member: Member, use_default: bool = True) -> int:
        kudos = await self.labels.get(
            f"member[{member.guild.id}]", member.id, "lifetime_kudos", default=None
        )
        if kudos is None and use_default:
            kudos = await self.get_kudos(member)
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

    async def _send_message_to_ledger(
        self, guild: Guild, kudos: int, message: str, image_url: Optional[str] = None
    ):
        channel = await self.get_ledger_channel(guild)
        if channel:
            action = "Gave" if kudos > 0 else "Took"
            embed = self.create_embed(guild, f"{message}", f"{action} {kudos} kudos!!!")
            if image_url:
                embed.set_thumbnail(url=image_url)
            await channel.send(embed=embed)
