from collections import defaultdict
from datetime import datetime, timedelta
from discord import Guild, Member, Message, RawReactionActionEvent, TextChannel, utils
from extensions.help_channels.channel_manager import ChannelManager
import asyncio
import dippy.labels


class HelpRotatorExtension(dippy.Extension):
    client: dippy.client.Client
    log: dippy.logging.Logging
    labels: dippy.labels.storage.StorageInterface
    manager: ChannelManager

    def __init__(self):
        super().__init__()
        self._claim_attempts: dict[int, list[datetime]] = defaultdict(list)
        self.client.loop.create_task(self.setup_cleanup())

    @dippy.Extension.listener("guild_join")
    async def on_guild_added_setup_cleanup(self, guild: Guild):
        self._setup_cleanup(guild)

    async def setup_cleanup(self):
        await self.client.wait_for("ready")
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
        if not categories or categories["getting-help"] != category.id:
            return

        await self.manager.update_help_channel(message.channel, message.author)

    @dippy.Extension.listener("raw_reaction_add")
    async def on_reaction_add_get_help(self, reaction: RawReactionActionEvent):
        emoji = reaction.emoji.name
        if emoji not in self.manager.reaction_topics and emoji != "🙋":
            return

        channel: TextChannel = self.client.get_channel(reaction.channel_id)
        categories = await self.manager.get_categories(channel.guild)
        if channel.category.id != categories["get-help"]:
            return

        member = channel.guild.get_member(
            reaction.user_id
        ) or await channel.guild.fetch_member(reaction.user_id)
        if member.bot:
            return

        self._claim_attempts[member.id].append(datetime.now())

        message = await channel.fetch_message(reaction.message_id)
        if not self._allow_claim_attempt(member):
            await message.remove_reaction(reaction.emoji, member)
            return

        last_claimed, channel_id = await self.labels.get(
            "user", member.id, "last-claimed-channel", (None, None)
        )
        if last_claimed:
            last_claimed = datetime.fromisoformat(last_claimed)
            if datetime.utcnow() - last_claimed < timedelta(hours=6):
                claimed_channel = channel.guild.get_channel(channel_id)
                await claimed_channel.send(
                    f"{member.mention} please use this channel for your question.",
                    delete_after=30,
                )
                await channel.send(
                    f"You've already claimed {claimed_channel.mention}, please use that channel. If you need to change "
                    f"the topic ask a helper.",
                    delete_after=15,
                )
                await message.remove_reaction(emoji, member)
                categories = await self.manager.get_categories(channel.guild)
                if claimed_channel.category.id == categories["help-archive"]:
                    await self.manager.update_archived_channel(claimed_channel, member)
                    await claimed_channel.purge(
                        after=datetime.now() - timedelta(days=1),
                        check=lambda msg: msg.author.bot
                        and "moved to the archive" in msg.content,
                    )
                return

        await message.edit(content="*Claiming channel for you, please standby*")
        await message.clear_reactions()
        await self.manager.update_get_help_channel(
            channel, member, self.manager.reaction_topics.get(emoji, "")
        )

    @dippy.Extension.listener("raw_reaction_add")
    async def on_reaction_add_archive(self, reaction: RawReactionActionEvent):
        emoji = reaction.emoji.name
        if emoji != "✅":
            return

        channel: TextChannel = self.client.get_channel(reaction.channel_id)
        categories = await self.manager.get_categories(channel.guild)
        if channel.category.id != categories["help-archive"]:
            return

        member = channel.guild.get_member(reaction.user_id)
        if member.bot:
            return

        owner = await self.manager.get_owner(channel)
        helper = utils.get(channel.guild.roles, name="helpers")
        if member != owner and helper not in member.roles:
            return

        await self.manager.update_archived_channel(channel, owner)
        await (await channel.fetch_message(reaction.message_id)).delete()

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

    def _allow_claim_attempt(self, member: Member) -> bool:
        now = datetime.now()
        attempts = 0
        for attempt in self._claim_attempts[member.id].copy():
            if attempt < now - timedelta(minutes=30):
                self._claim_attempts[member.id].remove(attempt)
            else:
                attempts += 1
        return attempts < 2

    def _setup_cleanup(self, guild: Guild):
        self.log.info(f"Starting channel cleanup for {guild.name}")
        self.client.loop.create_task(self.guild_cleanup_task(guild))
