from aiohttp import ClientSession
from collections import deque
from datetime import datetime, timedelta, timezone
from nextcord import Embed, Guild, Member, Message, Role, TextChannel, utils
from nextcord.errors import NotFound
from nextcord.webhook import Webhook
from typing import Optional
import dippy
import re


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
        self.client.loop.create_task(self._scan_for_webhooks(message))
        await self._handle_spamming_violations(message.channel, message.author)

    async def _scan_for_webhooks(self, message: Message):
        webhooks = re.findall(
            r"https://discord\.com/api/webhooks/\d+/[a-zA-Z0-9-_]+", message.content
        )
        for webhook in webhooks:
            await self._delete_webhook(webhook)

        if webhooks:
            title = f"{len(webhooks)} Webhooks" if len(webhooks) > 1 else "A Webhook"
            hooks = "\n".join(f"`{hook}`" for hook in webhooks)
            await message.channel.send(
                embed=Embed(
                    title=f"🗑 Deleted {title}",
                    description=(
                        f"Anyone can send messages to a webhook. For this reason we call the delete method on all "
                        f"webhooks that we detect. You will need to create a new webhook to replace the ones we "
                        f"deleted. Be sure to not share your webhooks publicly."
                    ),
                    color=0xFF0000,
                ).add_field(name="Deleted Webhooks", value=hooks),
                reference=message,
            )

    async def _delete_webhook(self, webhook: str):
        async with ClientSession() as session:
            hook = Webhook.from_url(webhook, session=session)
            try:
                await hook.delete()
            except NotFound:
                pass  # Don't care, just want it gone

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

        now = datetime.now().astimezone(timezone.utc)
        since = min(oldest or now, now - timedelta(minutes=1)).astimezone(timezone.utc)
        for message in (
            message for message in self._message_buffer if message.author == member
        ):
            if since > message.created_at:
                break

            if now - timedelta(seconds=5) <= message.created_at:
                num_recent_messages += 1

            if now - timedelta(seconds=15) <= message.created_at:
                recent_channels.add(message.channel.id)

            if len(message.content) > 15:
                messages_last_minute.add(message.content)
                num_messages_checked += 1

        return (
            num_recent_messages,
            len(recent_channels),
            num_messages_checked - len(messages_last_minute),
        )
