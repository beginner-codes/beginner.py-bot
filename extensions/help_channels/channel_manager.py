from bevy import Injectable
from collections import defaultdict
from datetime import datetime, timedelta
from extensions.help_channels.topic_buttons import create_view
from functools import cached_property
from discord import (
    CategoryChannel,
    Embed,
    Guild,
    Member,
    TextChannel,
    utils,
)
from pathlib import Path
from typing import Any, Optional, Union
import asyncio
import dippy.client
import dippy.labels
import discord
import re


class ChannelManager(Injectable):
    client: dippy.client.Client
    labels: dippy.labels.storage.StorageInterface
    log: dippy.logging.Logging

    def __init__(self):
        self._categories = {}
        self._topics = {
            "c-langs": "🌵",
            "c": "🌵",
            "cs": "🌵",
            "cpp": "🌵",
            "java": "☕️",
            "kotlin": "☕️",
            "python": "🐍",
            "py": "🐍",
            "discord": "🐍",
            "game_development": "🕹",
            "html": "🌎",
            "javascript": "🌎",
            "js": "🌎",
            "php": "🌎",
            "css": "🌎",
            "web-dev": "🌎",
            "web_development": "🌎",
            "flask": "🐍🌎",
            "django": "🐍🌎",
            "fast-api": "🐍🌎",
            "react": "🌎",
            "hacking": "🚨",
            "os": "💾",
            "docker": "📦",
            "kubernetes": "📦",
            "k8s": "📦",
            "rpi": "🥧",
            "raspberry-pi": "🥧",
            "ml": "🧠",
            "machine-learning": "🧠",
            "machine_learning": "🧠",
            "homework": "📓",
            "discord_bot": "🤖",
            "windows-os": "🪟",
            "unix-os": "🖥",
        }
        self.reaction_topics = {
            "🐍": "python",
            "🌵": "c-langs",
            "🌎": "web-dev",
            "💾": "os",
            "☕": "java",
            "javascript": "javascript",
        }
        self._claim_attempts: dict[int, list[datetime]] = defaultdict(list)

    def add_claim_attempt(self, member: Member):
        self._claim_attempts[member.id].append(datetime.now())

    def clear_claim_attempts(self, member: Member):
        self._claim_attempts[member.id].clear()

    def get_claim_attempts(self, member: Member) -> int:
        if member.guild_permissions.administrator:
            return 0

        now = datetime.now()
        attempts = 0
        for attempt in self._claim_attempts[member.id].copy():
            if attempt < now - timedelta(minutes=30):
                self._claim_attempts[member.id].remove(attempt)
            else:
                attempts += 1
        return attempts

    @cached_property
    def disallowed_channel_prefixes(self) -> set[str]:
        file_path = Path(__file__).parent.parent.parent / "disallowed-prefixes.txt"
        with open(file_path, "r") as prefix_file:
            return {line.strip() for line in prefix_file if line.strip()}

    def allowed_topic(self, topic: str) -> bool:
        return topic.casefold() in self._topics

    def allowed_topics(self) -> list[str]:
        return sorted(self._topics)

    async def archive_channel(self, channel: TextChannel, remove_owner: bool = False):
        categories = await self.get_categories(channel.guild)
        category = channel.guild.get_channel(categories["help-archive"])
        owner = None
        if remove_owner:
            await self.set_owner(channel, None)
        else:
            owner = await self.get_owner(channel)

        beginner = utils.get(self.client.emojis, name="beginner")
        intermediate = utils.get(self.client.emojis, name="intermediate")
        expert = utils.get(self.client.emojis, name="expert")

        try:
            await channel.edit(
                category=category,
                position=category.channels[0].position,
                sync_permissions=True,
            )
        except discord.errors.HTTPException:
            await channel.send(
                embed=Embed(
                    title="Could Not Archive",
                    description=(
                        f"The archive is completely full, this channel will be archived when possible.\n\nDon't forget "
                        f"to give some kudos to show your appreciation by reacting to the most helpful people with "
                        f"{beginner}, {intermediate}, or {expert}!"
                    ),
                    color=0x990000,
                ).set_thumbnail(
                    url="https://cdn.discordapp.com/emojis/651959497698574338.png?v=1"
                )
            )
            return

        content = ["📜 This channel has been moved to the archive."]
        if owner:
            content.insert(0, owner.mention)
            content.append(
                f"You can reclaim it by reacting with a ♻️.\n\nDon't forget to give some kudos to show your "
                f"appreciation by reacting to the most helpful people with {beginner}, {intermediate}, or {expert}!"
            )
        message = await channel.send(" ".join(content))
        if owner:
            await message.add_reaction("♻️")

    async def cleanup_help_channels(self, guild: Guild):
        categories = await self.get_categories(guild)
        if not categories:
            return

        channels = []
        for channel in guild.get_channel(categories["getting-help"]).channels:
            last_active = await self.get_last_active(channel)
            channels.append((channel, last_active))

        now = datetime.utcnow()
        channels = sorted(channels, key=lambda item: item[1], reverse=True)
        self.log.info(
            f"Checking {len(channels)} channels to find any that need to be archived"
        )
        num_channels = len(channels)
        while num_channels > 15 and channels:
            channel, last_active = channels.pop()
            age = (now - last_active) / timedelta(hours=1)
            owner = await self.get_owner(channel)
            if (
                not owner
                or age >= 24
                or (age >= 12 and num_channels >= 20)
                or (age >= 6 and num_channels >= 25)
            ):
                await self.archive_channel(channel)
                num_channels -= 1

    async def create_new_channel(self, category: CategoryChannel):
        channel = await category.create_text_channel(name="🙋get-help")
        await self.set_last_active(channel)

    async def get_categories(self, guild: Guild) -> dict[str, int]:
        if not self._categories.get(guild):
            categories = await self._get_guild_label(guild, "help-categories", {})
            self._categories[guild] = categories

        return self._categories[guild]

    async def is_help_channel(self, channel: TextChannel) -> bool:
        categories = await self.get_categories(channel.guild)
        return channel.category.id == categories["getting-help"]

    async def get_last_active(self, channel: TextChannel) -> datetime:
        last_active = await self.labels.get(
            "text_channel",
            channel.id,
            "last-active",
        )
        return (
            datetime.fromisoformat(last_active)
            if last_active
            else datetime.utcfromtimestamp(0)
        )

    async def set_last_active(self, channel: TextChannel):
        await self.labels.set(
            "text_channel", channel.id, "last-active", datetime.utcnow().isoformat()
        )

    async def get_owner(
        self, channel: TextChannel, just_id: bool = False
    ) -> Union[Member, int]:
        owner_id = await self.labels.get("text_channel", channel.id, "owner")
        if just_id:
            return owner_id
        return channel.guild.get_member(owner_id)

    async def set_owner(self, channel: TextChannel, owner: Optional[Member]):
        owner_id = owner.id if owner else -1
        await self.labels.set("text_channel", channel.id, "owner", owner_id)

    async def set_categories(self, guild: Guild, categories: dict[str, int]):
        await self._set_guild_label(guild, "help-categories", categories)
        self._categories[guild] = categories

    async def set_channel_topic(self, channel: TextChannel, topic: str):
        owner = await self.get_owner(channel)
        await self.labels.set("text_channel", channel.id, "topic", topic)
        icon = self._topics.get(topic, "🙋")
        await channel.edit(
            name=self._generate_channel_title(owner.display_name, topic, icon)
        )
        await channel.send(f"Topic changed to {icon}{topic}", delete_after=10)

    async def setup_help_channel(self, category: CategoryChannel):
        channels = await self.get_archive_channels(category.guild)
        channel = channels[0]
        await channel.edit(name=f"🙋get-help", category=category, sync_permissions=True)
        await channel.send(
            view=create_view(),
            embed=Embed(
                title="Claim Your Own Help Channel",
                description=(
                    "You can ask your question after you select what programming language or topics (up to 2) you need "
                    "help with.\n\nOnce you click the 'Claim Channel' button you will be taken to your help channel, "
                    "**it may take a couple seconds** so be patient."
                ),
                color=0x00FF66,
            ),
        )

        if len(channels) == 1:
            await self.archive_channel(
                (await self._get_help_channels(category.guild))[0]
            )

    async def update_archived_channel(self, channel: TextChannel, author: Member):
        owner = await self.labels.get("text_channel", channel.id, "owner")
        if author.id != owner:
            return

        categories = await self._get_guild_label(channel.guild, "help-categories")
        helping_category = self.client.get_channel(categories["getting-help"])
        options = {"category": helping_category, "sync_permissions": True}
        if helping_category.channels:
            options["position"] = helping_category.channels[0].position

        help_channels = await self._get_help_channels(channel.guild)
        if len(help_channels) == 50:
            await self.archive_channel(help_channels[0])

        await channel.edit(**options)
        await channel.send("🗂 Channel has been removed from the archive")
        await self.update_help_channel(channel, author)

    async def update_help_channel(self, channel: TextChannel, author: Member):
        owner = await self.labels.get(
            "text_channel", channel.id, "owner", default=author.id
        )
        if owner != author.id:
            return

        top_channel = channel.category.channels[0]
        if top_channel != channel:
            last_active = datetime.fromisoformat(
                str(
                    await self.labels.get(
                        "text_channel",
                        channel.id,
                        "last-active",
                    )
                )
            )
            if (datetime.utcnow() - last_active) >= timedelta(minutes=15):
                await channel.edit(position=top_channel.position)

        await self.labels.set(
            "text_channel", channel.id, "last-active", datetime.utcnow().isoformat()
        )

    async def update_get_help_channel(
        self,
        channel: TextChannel,
        owner: Member,
        language: Optional[str],
        topics: Optional[list[str]] = None,
    ):
        categories = await self.get_categories(channel.guild)
        topic, icon = self._build_topic(language, topics)
        name = self._generate_channel_title(owner.display_name, topic, icon)
        helping_category = self.client.get_channel(categories["getting-help"])
        help_category: CategoryChannel = self.client.get_channel(categories["get-help"])

        topic = language
        if language and topics:
            topic = f"{language} - {', '.join(topics)}"
        elif topics:
            topic = ", ".join(topics)

        topic = topic.replace("_", " ").title()

        args = {
            "reason": f"Claimed by {owner.display_name} for a question",
            "name": name,
            "topic": f"Helping {owner.display_name} with {topic}",
            "category": helping_category,
            "sync_permissions": True,
        }
        if helping_category.channels:
            args["position"] = helping_category.channels[0].position

        pins = await channel.pins()

        new_message = await channel.send(
            f"{owner.mention}",
            embed=Embed(
                title=f"{owner.display_name}#{owner.discriminator} Ask Your Question Here",
                description=(
                    "Current topic is " + topic + "\n\n"
                    "Make sure to be as clear as possible and provide as many details as you can:\n• Show your code 💻"
                    "\n• Show any errors you've gotten ⚠️\n• Etc.\n*Someone will try to help you when they get a "
                    "chance.*\n\nOnce you no longer need help use `!done` to close the channel."
                ),
                color=0x00FF66,
            ),
        )

        if len(channel.category.channels) == 50:
            help_channels = await self._get_help_channels(channel.guild)
            await self.archive_channel(help_channels[0])

        await channel.edit(**args)

        tasks = [
            self.labels.set(
                "user",
                owner.id,
                "last-claimed-channel",
                (datetime.utcnow().isoformat(), channel.id),
            ),
            self.labels.set("text_channel", channel.id, "owner", owner.id),
            self.labels.set(
                "text_channel", channel.id, "last-active", datetime.utcnow().isoformat()
            ),
            new_message.pin(reason="Jump to start of current help question"),
        ]

        if pins:
            tasks.extend(pin.unpin() for pin in pins)

        try:
            message, *_ = await channel.history(limit=1, before=new_message).flatten()
        except ValueError:
            pass
        else:
            tasks.append(message.delete())
        await asyncio.gather(*tasks)
        count = len(help_category.channels) - 1
        while count < 2:
            await self.setup_help_channel(help_category)
            count += 1

    async def get_archive_channels(self, guild: Guild) -> list[TextChannel]:
        archive = guild.get_channel((await self.get_categories(guild))["help-archive"])
        channels = []
        for channel in archive.channels:
            last_active = await self.get_last_active(channel)
            channels.append((channel, last_active))

        return [channel for channel, _ in sorted(channels, key=lambda item: item[1])]

    async def _get_help_channels(self, guild: Guild) -> list[TextChannel]:
        archive = guild.get_channel((await self.get_categories(guild))["getting-help"])
        channels = []
        for channel in archive.channels:
            last_active = await self.get_last_active(channel)
            channels.append((channel, last_active))

        return [channel for channel, _ in sorted(channels, key=lambda item: item[1])]

    def _generate_channel_title(self, name: str, topic: str, icon: str = "🙋") -> str:
        slug = self.sluggify(name, sep="")
        prefix = self._get_prefix(slug)
        topic = self.sluggify(topic)
        return f"{icon}{prefix}-{topic}"

    async def _get_guild_label(
        self, guild: Guild, label: str, default: Any = None
    ) -> Any:
        return await self.labels.get("guild", guild.id, label, default=default)

    async def _set_guild_label(self, guild: Guild, label: str, value: Any):
        await self.labels.set("guild", guild.id, label, value)

    def _get_prefix(self, slug: str) -> str:
        prefix = slug[:3]
        if prefix in self.disallowed_channel_prefixes:
            prefix = slug[:2]
        return prefix

    def sluggify(self, text: str, *, sep: str = "-") -> str:
        if not text:
            return ""

        parts = re.findall(r"[\w\d]+", text.replace("++", "pp").casefold())
        return sep.join(parts)

    def _build_topic(self, language: Optional[str], topics: Optional[list[str]]):
        topic = "_".join(topics) if topics else ""
        icon = []
        if language:
            topic = self.sluggify(language)
            icon.append(self._topics[topic])

        if topics:
            icon.extend(
                self._topics[slug]
                for t in topics
                if (slug := self.sluggify(t)) in self._topics
            )

        return self.sluggify(topic), "".join(icon)
