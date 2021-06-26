from collections import deque
from datetime import datetime, timedelta
from discord import Guild, Member, Message, Role, TextChannel, utils
from typing import Optional
import dippy


class AutoModExtension(dippy.Extension):
    client: dippy.Client

    def __init__(self):
        super().__init__()
        self._message_buffer = deque(maxlen=1000)
        self._warned = {}
        self._muting = set()

    def mute_role(self, guild: Guild) -> Role:
        return utils.get(guild.roles, name="Muted")

    @dippy.Extension.listener("message")
    async def on_message(self, message: Message):
        if message.author.bot:
            return

        if message.channel.permissions_for(message.author).manage_messages:
            return

        if (
            message.author.id in self._muting
            or self.mute_role(message.guild) in message.author.roles
        ):
            return

        self._message_buffer.appendleft(message)
        await self._handle_spamming_violations(message.channel, message.author)

    async def _handle_spamming_violations(self, channel: TextChannel, member: Member):
        last_warned = self._warned[member.id] if member.id in self._warned else None
        should_mute = last_warned and datetime.utcnow() - last_warned <= timedelta(
            minutes=2
        )
        (
            num_messages_last_five_seconds,
            num_channels_last_fifteen_seconds,
            num_duplicate_messages,
        ) = self._metrics_on_messages_from_member(member, last_warned)

        too_many_messages = num_messages_last_five_seconds > 5
        too_many_channels = num_channels_last_fifteen_seconds > 3
        too_many_duplicates = num_duplicate_messages > 1

        if not too_many_messages and not too_many_channels and not too_many_duplicates:
            return

        action_description = []
        if should_mute:
            action_description.append(
                f"{member.mention} you're being muted until the mods can review your behavior:\n"
            )
            if too_many_messages:
                action_description.append("- Message spamming\n")
            if too_many_channels:
                action_description.append("- Spamming in multiple channels\n")
            if too_many_duplicates:
                action_description.append("- Sending duplicate messages\n")

        else:
            if too_many_messages:
                action_description.append(" spamming messages")
            if too_many_channels:
                action_description.append(" messaging in so many channels")
            if too_many_duplicates:
                action_description.append(" sending duplicate messages")

            if len(action_description) > 1:
                action_description[-1] = f" and{action_description[-1]}"
            if len(action_description) > 2:
                action_description = [",".join(action_description)]

            action_description.insert(0, f"{member.mention} please stop")

        if should_mute:
            self._muting.add(member.id)
            await member.add_roles(self.mute_role(member.guild))
            self._muting.remove(member.id)

        m: Message = await channel.send("".join(action_description))
        if should_mute:
            mods: Role = channel.guild.get_role(644390354157568014)
            await self.client.get_channel(728249959098482829).send(
                f"{mods.mention} please review {member.mention}'s behavior in {channel.mention} {m.jump_url}.\nUse "
                f"`!unmute` to remove their mute."
            )
        self._warned[member.id] = datetime.utcnow()

    def _metrics_on_messages_from_member(
        self, member: Member, oldest: Optional[datetime] = None
    ) -> tuple[int, int, int]:
        num_messages_checked = 0
        num_recent_messages = 0
        recent_channels = set()
        messages_last_minute = set()

        now = datetime.utcnow()
        since = min(oldest or now, now - timedelta(minutes=1))
        for message in (
            message for message in self._message_buffer if message.author == member
        ):
            if since > message.created_at:
                break

            if now - timedelta(seconds=5) <= message.created_at:
                num_recent_messages += 1

            if now - timedelta(seconds=15) <= message.created_at:
                recent_channels.add(message.channel.id)

            if message.content.length > 15:
                messages_last_minute.add(message.content)

            num_messages_checked += 1

        return (
            num_recent_messages,
            len(recent_channels),
            num_messages_checked - len(messages_last_minute),
        )
