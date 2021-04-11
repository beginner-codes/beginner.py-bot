from datetime import datetime, timedelta
from discord import Guild, Message, RawReactionActionEvent, TextChannel
from extensions.help_channels.channel_manager import ChannelManager
import asyncio
import dippy.labels


class HelpRotatorExtension(dippy.Extension):
    client: dippy.client.Client
    log: dippy.logging.Logging
    labels: dippy.labels.storage.StorageInterface
    manager: ChannelManager

    @dippy.Extension.listener("guild_join")
    async def on_guild_added_setup_cleanup(self, guild: Guild):
        self._setup_cleanup(guild)

    @dippy.Extension.listener("ready")
    async def on_ready_setup_cleanup(self):
        for guild in self.client.guilds:
            self._setup_cleanup(guild)

    @dippy.Extension.listener("message")
    async def on_message(self, message: Message):
        category = message.channel.category
        if not category or not category.guild:
            return

        if message.author.bot:
            return

        if message.content.startswith("!"):
            return

        categories = await self.manager.get_categories(category.guild)
        if not categories:
            return

        actions = {
            "help-archive": self.manager.update_archived_channel,
            "getting-help": self.manager.update_help_channel,
        }
        for help_type, category_id in categories.items():
            if category.id == category_id and help_type in actions:
                await actions[help_type](message.channel, message.author)
                break

    @dippy.Extension.listener("raw_reaction_add")
    async def on_reaction_add(self, reaction: RawReactionActionEvent):
        emoji = reaction.emoji.name
        if emoji not in self.manager.reaction_topics and emoji != "🙋":
            return

        channel: TextChannel = self.client.get_channel(reaction.channel_id)
        categories = await self.manager.get_categories(channel.guild)

        if channel.category.id != categories["get-help"] or "hidden" in channel.name:
            return

        member = await channel.guild.fetch_member(reaction.user_id)
        if member.bot:
            return

        last_claimed, channel_id = await self.labels.get(
            "user", member.id, "last-claimed-channel", (None, None)
        )
        if last_claimed:
            last_claimed = datetime.fromisoformat(last_claimed)
            if datetime.utcnow() - last_claimed < timedelta(minutes=15):
                message, *_ = await asyncio.gather(
                    channel.fetch_message(reaction.message_id),
                    channel.guild.get_channel(channel_id).send(
                        f"{member.mention} please use this channel for your question."
                    ),
                )
                await message.remove_reaction(emoji, member)
                return

        await self.manager.update_get_help_channel(
            channel, member, self.manager.reaction_topics.get(emoji, "")
        )

    async def guild_cleanup_task(self, guild: Guild):
        now = datetime.utcnow()
        next_cleanup = (
            now.replace(second=0, microsecond=0)
            + timedelta(minutes=15 - now.minute % 15 if now.minute % 15 else 15)
            - now
        )
        self.log.info(
            f"Next cleanup for {guild.name} at {(now + next_cleanup).isoformat()}"
        )
        await asyncio.sleep(next_cleanup.total_seconds())
        self.log.info(f"Cleaning up channels for {guild.name}")
        self.client.loop.create_task(self.guild_cleanup_task(guild))
        await self.manager.cleanup_help_channels(guild)

    def _setup_cleanup(self, guild: Guild):
        self.log.info(f"Starting channel cleanup for {guild.name}")
        self.client.loop.create_task(self.guild_cleanup_task(guild))
