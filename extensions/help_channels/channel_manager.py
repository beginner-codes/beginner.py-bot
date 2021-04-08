from bevy import Injectable
from datetime import datetime
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
        self._reaction_topics = {
            "🐍": "python",
            "🌵": "c-langs",
            "🌎": "web-dev",
            "💾": "os",
        }

    async def archive_channel(self, channel: TextChannel):
        categories = await self.get_categories(channel.guild)
        owner = await self.get_owner(channel)

        await channel.edit(
            category=channel.guild.get_channel(categories["help-archive"]),
            overwrites={
                owner: PermissionOverwrite(send_messages=True),
                channel.guild.default_role: PermissionOverwrite(send_messages=False),
            },
        )

        beginner = utils.get(self.client.emojis, name="beginner")
        intermediate = utils.get(self.client.emojis, name="intermediate")
        expert = utils.get(self.client.emojis, name="expert")
        await channel.send(
            f"{owner.mention} This channel has been moved to the archive.\n\nDon't forget to give some kudos to show "
            f"your appreciation by reacting with {beginner}, {intermediate}, or {expert}!"
        )

    async def create_help_channel(self, category: CategoryChannel, hidden: bool = True):
        overwrites = {}
        if hidden:
            overwrites[category.guild.default_role] = PermissionOverwrite(
                read_messages=False
            )

        channel = await category.create_text_channel(
            name=f"🙋get-help{'-hidden' if hidden else ''}", overwrites=overwrites
        )
        message = await channel.send(
            embed=Embed(
                title="Get Help Here",
                description=(
                    "React with the topic that most closely fits what you need help with. This will claim the channel "
                    "and move it to the help area where you can ask your question.\n\n**Categories**\n🐍 Python/"
                    "Discord.py\n🌵 C/C++/C#\n🌎 Web Dev/JavaScript/HTML\n💾 OS/Docker/Kubernetes\n🙋 General Help"
                ),
                color=0x00FF66,
            )
        )

        emojis = list(self._reaction_topics)
        emojis.append("🙋")
        await asyncio.gather(*(message.add_reaction(emoji=emoji) for emoji in emojis))

    async def get_categories(self, guild: Guild):
        if not self._categories.get(guild):
            categories = await self._get_guild_label(guild, "help-categories")
            self._categories[guild] = categories

        return self._categories[guild]

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

    async def update_archived_channel(self, channel: TextChannel, author: Member):
        owner = await self.labels.get("text_channel", channel.id, "owner")
        if author.id != owner:
            return

        categories = await self._get_guild_label(channel.guild, "help-categories")
        helping_category = self.client.get_channel(categories["getting-help"])
        options = {
            "category": helping_category,
        }
        if helping_category.channels:
            options["position"] = helping_category.channels[0].position
        await channel.edit(**options)
        await self.update_help_channel(channel, author)

    async def update_help_channel(self, channel: TextChannel, author: Member):
        owner = await self.labels.get(
            "text_channel", channel.id, "owner", default=author.id
        )
        if owner == author.id:
            if channel.category.channels[0] != channel:
                last_active = datetime.fromisoformat(
                    str(
                        await self.labels.get(
                            "text_channel",
                            channel.category.channels[0].id,
                            "last-active",
                        )
                    )
                )
                if (datetime.utcnow() - last_active).total_seconds() > 15:
                    await channel.edit(position=channel.category.channels[0].position)

            await self.labels.set(
                "text_channel", channel.id, "last-active", datetime.utcnow().isoformat()
            )

    async def update_get_help_channel(
        self, channel: TextChannel, owner: Member, topic: Optional[str] = None
    ):
        categories = await self.get_categories(channel.guild)
        name = self._generate_channel_title(owner.display_name, topic)
        helping_category = self.client.get_channel(categories["getting-help"])
        help_category: CategoryChannel = self.client.get_channel(categories["get-help"])

        await asyncio.gather(
            self.labels.set("text_channel", channel.id, "owner", owner.id),
            self.labels.set(
                "text_channel", channel.id, "last-active", datetime.utcnow().isoformat()
            ),
            channel.edit(
                reason=f"Claimed by {owner.display_name} for a question",
                name=name,
                category=helping_category,
                position=helping_category.channels[0].position,
                sync_permissions=True,
            ),
            help_category.channels[-2].edit(
                sync_permissions=True,
                name=help_category.channels[-2].name.removesuffix("-hidden"),
            ),
            channel.purge(limit=1, oldest_first=True),
            channel.send(
                f"{owner.mention} ask your question here. Make sure to be as clear as possible and provide as "
                f"many details as you can (code, errors, etc.), someone will try to help you when they get a "
                f"chance."
            ),
        )

        await self.create_help_channel(help_category, hidden=True),

    def _generate_channel_title(self, name: str, topic: str, icon: str = "🙋") -> str:
        name = self.sluggify(name)
        topic = self.sluggify(topic)
        return f"{icon}helping-{name}" + f"-with-{topic}" * bool(topic)

    async def _get_guild_label(self, guild: Guild, label: str) -> Any:
        return await self.labels.get("guild", guild.id, label)

    async def _set_guild_label(self, guild: Guild, label: str, value: Any):
        await self.labels.set("guild", guild.id, label, value)

    def sluggify(self, text: str) -> str:
        if not text:
            return ""

        parts = re.findall(r"[\w\d]+", text)
        return "-".join(parts)
