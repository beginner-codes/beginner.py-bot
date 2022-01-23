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
        if (
            emoji not in self.manager.reaction_topics and emoji != "🙋"
        ) or reaction.channel_id == 742209536500170812:
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

        self.manager.add_claim_attempt(member)

        message = await channel.fetch_message(reaction.message_id)
        if not self._allow_claim_attempt(member):
            await message.remove_reaction(reaction.emoji, member)
            return

        last_claimed, channel_id = await self.labels.get(
            "user", member.id, "last-claimed-channel", (None, None)
        )
        if (
            last_claimed
            and await self.manager.get_owner(channel.guild.get_channel(channel_id))
            == member
        ):
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
                await message.remove_reaction(reaction.emoji, member)
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
        if emoji not in "✅♻️":
            return

        channel: TextChannel = self.client.get_channel(reaction.channel_id)
        categories = await self.manager.get_categories(channel.guild)
        if channel.category.id != categories["help-archive"]:
            return

        member = channel.guild.get_member(reaction.user_id)
        if not member or member.bot:
            return

        owner = await self.manager.get_owner(channel)
        if not owner:
            await channel.send("User is no longer a member here", delete_after=5)
            return

        staff = utils.get(channel.guild.roles, name="staff")
        if member != owner and staff not in member.roles:
            return

        await self.manager.update_archived_channel(channel, owner)
        await (await channel.fetch_message(reaction.message_id)).delete()

    def guild_cleanup_task(self, guild: Guild):
        now = datetime.utcnow()
        next_cleanup = (
            now.replace(second=0, microsecond=0)
            + timedelta(minutes=5 - now.minute % 5 if now.minute % 5 else 5)
            - now
        )
        self.log.info(
            f"Next cleanup for {guild.name} at {(now + next_cleanup).isoformat()}"
        )

        self.client.loop.call_later(
            next_cleanup.total_seconds(), self.do_guild_cleanup, guild
        )

    def do_guild_cleanup(self, guild):
        self.log.info(f"Cleaning up channels for {guild.name}")
        self.guild_cleanup_task(guild)
        self.client.loop.create_task(self.manager.cleanup_help_channels(guild))

    def _allow_claim_attempt(self, member: Member) -> bool:
        return self.manager.get_claim_attempts(member) < 2

    def _setup_cleanup(self, guild: Guild):
        self.log.info(f"Starting channel cleanup for {guild.name}")
        self.guild_cleanup_task(guild)
