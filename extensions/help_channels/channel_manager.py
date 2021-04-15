from bevy import Injectable
from datetime import datetime, timedelta
from discord import (
    CategoryChannel,
    Embed,
    Guild,
    Member,
    PermissionOverwrite,
    TextChannel,
    utils,
)
from typing import Any, Optional, Union
import asyncio
import dippy.labels
import dippy.client
import re


class ChannelManager(Injectable):
    client: dippy.client.Client
    labels: dippy.labels.storage.StorageInterface

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
            "html": "🌎",
            "javascript": "🌎",
            "js": "🌎",
            "php": "🌎",
            "web-dev": "🌎",
            "hacking": "🚨",
            "os": "💾",
            "docker": "💾",
            "kubernetes": "💾",
            "k8s": "💾",
        }
        self.reaction_topics = {
            "🐍": "python",
            "🌵": "c-langs",
            "🌎": "web-dev",
            "💾": "os",
        }

    async def archive_channel(self, channel: TextChannel):
        categories = await self.get_categories(channel.guild)
        category = channel.guild.get_channel(categories["help-archive"])
        owner = await self.get_owner(channel)
        overwrites = category.overwrites.copy()
        overwrites[owner] = PermissionOverwrite(send_messages=True)
        await channel.edit(
            category=category,
            overwrites=overwrites,
        )

        beginner = utils.get(self.client.emojis, name="beginner")
        intermediate = utils.get(self.client.emojis, name="intermediate")
        expert = utils.get(self.client.emojis, name="expert")
        await channel.send(
            f"{owner.mention} This channel has been moved to the archive. You can reclaim it just by sending a message."
            f"\n\nDon't forget to give some kudos to show your appreciation by reacting with {beginner}, {intermediate}"
            f", or {expert}!"
        )

    async def cleanup_help_channels(self, guild: Guild):
        categories = await self.get_categories(guild)
        if not categories:
            return

        channels = []
        for channel in guild.get_channel(categories["getting-help"]).channels:
            last_active = datetime.fromisoformat(
                str(
                    await self.labels.get(
                        "text_channel",
                        channel.id,
                        "last-active",
                        (datetime.utcnow() - timedelta(days=1)).isoformat(),
                    )
                )
            )
            channels.append((channel, last_active))

        now = datetime.utcnow()
        channels = sorted(channels, key=lambda item: item[1], reverse=True)
        while len(channels) > 10:
            channel, last_active = channels.pop()
            age = (now - last_active) / timedelta(hours=1)
            num = len(channels)
            if age > 24 or (age > 12 and num > 15) or (age > 6 and num > 20):
                await self.archive_channel(channel)
            else:
                break

    async def create_new_channel(self, category: CategoryChannel):
        channel = await category.create_text_channel(name="🙋get-help")
        await self.set_last_active(channel)

    async def get_categories(self, guild: Guild) -> dict[str, int]:
        if not self._categories.get(guild):
            categories = await self._get_guild_label(guild, "help-categories")
            self._categories[guild] = categories

        return self._categories[guild]

    async def get_last_active(self, channel: TextChannel) -> datetime:
        return datetime.fromisoformat(
            await self.labels.get(
                "text_channel",
                channel.id,
                "last-active",
            )
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
        return await channel.guild.fetch_member(owner_id)

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

    async def setup_help_channel(self, category: CategoryChannel):
        channels = await self._get_archive_channels(category.guild)
        channel = channels[0]
        await channel.edit(name=f"🙋get-help", category=category)
        message = await channel.send(
            embed=Embed(
                title="Get Help Here",
                description=(
                    "React with the topic that most closely fits what you need help with. This will claim the channel "
                    "and move it to the help area where you can ask your question."
                ),
                color=0x00FF66,
            ).add_field(
                name="Categories",
                value=(
                    "🐍 Python/Discord.py\n🌵 C/C++/C#\n🌎 Web Dev/JavaScript/HTML\n💾 OS/Docker/Kubernetes\n🙋 General"
                    " Help"
                ),
            )
        )

        emojis = list(self.reaction_topics)
        emojis.append("🙋")
        await asyncio.gather(*(message.add_reaction(emoji=emoji) for emoji in emojis))

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
        await channel.edit(**options)
        await channel.send("🗂 Channel has been removed from the archive")
        await self.update_help_channel(channel, author)

    async def update_help_channel(self, channel: TextChannel, author: Member):
        owner = await self.labels.get(
            "text_channel", channel.id, "owner", default=author.id
        )
        if owner == author.id:
            for chan in channel.category.channels:
                if chan == channel:
                    break
                last_active = datetime.fromisoformat(
                    str(
                        await self.labels.get(
                            "text_channel",
                            chan.id,
                            "last-active",
                        )
                    )
                )
                if (datetime.utcnow() - last_active).total_seconds() > 15:
                    await channel.edit(position=chan.position)
                    break

            await self.labels.set(
                "text_channel", channel.id, "last-active", datetime.utcnow().isoformat()
            )

    async def update_get_help_channel(
        self, channel: TextChannel, owner: Member, topic: Optional[str] = None
    ):
        categories = await self.get_categories(channel.guild)
        name = self._generate_channel_title(
            owner.display_name, topic, self._topics.get(topic, "🙋")
        )
        helping_category = self.client.get_channel(categories["getting-help"])
        help_category: CategoryChannel = self.client.get_channel(categories["get-help"])

        args = {
            "reason": f"Claimed by {owner.display_name} for a question",
            "name": name,
            "topic": f"Helping {owner.display_name} with their question!",
            "category": helping_category,
            "sync_permissions": True,
        }
        if helping_category.channels:
            args["position"] = helping_category.channels[0].position

        message, *_ = await channel.history(limit=1).flatten()

        await asyncio.gather(
            message.delete(),
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
            channel.edit(**args),
            channel.send(
                f"{owner.mention} ask your question here.\nMake sure to be as clear as possible and provide as many "
                f"details as you can:\n• Code 💻\n• Errors ⚠️\n• Etc.\n*Someone will try to help you when they get a "
                f"chance.*"
            ),
            self.setup_help_channel(help_category),
        )

    async def _get_archive_channels(self, guild: Guild) -> list[TextChannel]:
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
        name = self.sluggify(name)
        topic = self.sluggify(topic)
        return "-".join((f"{icon}{name}", topic))

    async def _get_guild_label(self, guild: Guild, label: str) -> Any:
        return await self.labels.get("guild", guild.id, label)

    async def _set_guild_label(self, guild: Guild, label: str, value: Any):
        await self.labels.set("guild", guild.id, label, value)

    def sluggify(self, text: str) -> str:
        if not text:
            return ""

        parts = re.findall(r"[\w\d]+", text)
        return "-".join(parts)
