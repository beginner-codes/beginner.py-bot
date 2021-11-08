import re

from datetime import datetime, timedelta, timezone
from discord import Embed, Member, Message, TextChannel
from extensions.help_channels.channel_manager import ChannelManager
import dippy.client


class HelpChannelModerationExtension(dippy.Extension):
    client: dippy.client.Client
    manager: ChannelManager

    bad_words = {
        "asshole": 60,
        "@ss": 60,
        "bitch": 60,
        "dumb": 30,
        "fuck": 60,
        "f@ck": 60,
        "gay": 60,
        "idiot": 30,
        "mf": 60,
        "nigger": 60,
        "retard": 60,
        "shutup": 20,
        "stupid": 30,
    }

    @dippy.Extension.listener("message")
    async def on_help_channel_message(self, message: Message):
        if message.author.bot:
            return

        if not message.guild:
            return

        if not await self.manager.is_help_channel(message.channel):
            return

        content = str(message.clean_content)
        if self.score_bad_words(content.casefold()) >= 1.0:
            await self.send_alert(message, "possibly being aggressive (bad words)")
            return

        if len(content) > 5 and self.get_caps_ratio(content) >= 0.5:
            await self.send_alert(message, "possibly being aggressive (lots of caps)")
            return

    async def can_alert(self, channel: TextChannel, member: Member) -> bool:
        last_alert = await self.get_last_alert(channel, member)
        now = datetime.utcnow().astimezone(timezone.utc)
        return last_alert - now >= timedelta(minutes=15)

    async def flag_message(self, message: Message):
        await message.add_reaction("🚩")

    def get_caps_ratio(self, content: str) -> float:
        letters = [c for c in content if c.isalpha()]
        return len([c for c in letters if c.isupper()]) / len(letters)

    async def get_last_alert(self, channel: TextChannel, member: Member) -> datetime:
        return datetime.fromtimestamp(
            await channel.get_label(f"last-alert[{member.id}]", default=0),
            tz=timezone.utc,
        )

    async def set_last_alert(self, channel: TextChannel, member: Member):
        await channel.set_label(
            f"last-alert[{member.id}]", datetime.utcnow().timestamp()
        )

    def score_bad_words(self, content: str) -> float:
        points = sum(
            self.bad_words[word]
            for word in re.findall(r"\w+", content)
            if word in self.bad_words
        )
        return points / 60

    async def send_alert(self, message: Message, description: str):
        await self.flag_message(message)

        if await self.can_alert(message.channel, message.author):
            await self.send_staff_alert(message, description)
            await self.set_last_alert(message.channel, message.author)

    async def send_staff_alert(self, message: Message, description: str):
        await self.client.get_channel(720663441966366850).send(
            embed=(
                Embed(
                    title="Possible Bad Behavior",
                    description=(
                        f"{message.author.mention} has been flagged in {message.channel.mention} for {description}."
                    ),
                    color=0xBB0000,
                )
                .add_field(
                    name="Details",
                    value=(
                        f"User: {message.author} ({message.author.id})\nChannel: {message.channel.mention}\nMessage: "
                        f"[Jump]({message.jump_url})"
                    ),
                    inline=False,
                )
                .add_field(
                    name="Message Content",
                    value=message.clean_content[:1000],
                    inline=False,
                )
            )
        )
