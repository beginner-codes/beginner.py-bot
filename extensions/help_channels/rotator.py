from collections import defaultdict
from datetime import datetime, timedelta
from discord import (
    Guild,
    Interaction,
    InteractionResponded,
    Member,
    Message,
    RawReactionActionEvent,
    TextChannel,
    utils,
)
from extensions.help_channels.channel_manager import ChannelManager
import dippy.labels
import nextcord.errors


class ChannelClaimTicket:
    def __init__(self):
        self.start = datetime.fromtimestamp(0)
        self._language = None
        self._topics = None

    @property
    def language(self):
        if datetime.now() - self.start > timedelta(minutes=15):
            self.__init__()

        return self._language

    @language.setter
    def language(self, value):
        self.start = datetime.now()
        self._language = value

    @property
    def topics(self):
        if datetime.now() - self.start > timedelta(minutes=15):
            self.__init__()

        return self._topics

    @topics.setter
    def topics(self, value):
        self.start = datetime.now()
        self._topics = value


class HelpRotatorExtension(dippy.Extension):
    client: dippy.client.Client
    log: dippy.logging.Logging
    labels: dippy.labels.storage.StorageInterface
    manager: ChannelManager

    def __init__(self):
        super().__init__()
        self.client.loop.create_task(self.setup_cleanup())
        self.claiming: dict[int, ChannelClaimTicket] = defaultdict(ChannelClaimTicket)

    @dippy.Extension.listener("guild_join")
    async def on_guild_added_setup_cleanup(self, guild: Guild):
        self._setup_cleanup(guild)

    async def setup_cleanup(self):
        await self.client.wait_for("ready")
        for guild in self.client.guilds:
            self._setup_cleanup(guild)

    @dippy.Extension.listener("message")
    async def on_message(self, message: Message):
        if not isinstance(message.channel, TextChannel):
            return

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

    @dippy.Extension.listener("interaction")
    async def on_get_help_interaction(self, interaction: Interaction):
        component_id = interaction.data["custom_id"]
        if not component_id.startswith("bc.help"):
            return

        try:
            ticket = self.claiming[interaction.user.id]

            if component_id == "bc.help.language":
                ticket.language = interaction.data["values"][0]

            elif component_id == "bc.help.topic":
                ticket.topics = interaction.data["values"]

            elif not ticket.language and not ticket.topics:
                await interaction.response.send_message(
                    f"{interaction.user.mention} you must select at least a language, a topic, or both.",
                    ephemeral=True,
                )

            elif component_id == "bc.help.claim_button": 
                await self._handle_help_channel_claim(interaction, ticket)

        finally:
            await self._do_ack(interaction.response)

    async def _do_ack(self, response: nextcord.InteractionResponse):
        if response.is_done():
            return

        try:
            await response.defer()
        except (InteractionResponded, nextcord.errors.HTTPException):
            pass

    async def _handle_help_channel_claim(
        self, interaction: Interaction, ticket: ChannelClaimTicket
    ):
        categories = await self.manager.get_categories(interaction.guild)
        member = interaction.guild.get_member(
            interaction.user.id
        ) or await interaction.guild.fetch_member(interaction.user.id)
        if member.bot:
            return

        self.manager.add_claim_attempt(member)

        if not self._allow_claim_attempt(member):
            await interaction.response.send_message(
                f"{member.mention} Please wait at a little while before attempting to claim a new help channel.",
                ephemeral=True,
            )
            return

        last_claimed, channel_id = await self.labels.get(
            "user", member.id, "last-claimed-channel", (None, None)
        )
        last_channel = interaction.guild.get_channel(channel_id)
        if last_channel and await self.manager.get_owner(last_channel) == member:
            last_claimed = datetime.fromisoformat(last_claimed)
            if datetime.utcnow() - last_claimed < timedelta(hours=6):
                claimed_channel = interaction.guild.get_channel(channel_id)
                await claimed_channel.send(
                    f"{member.mention} please use this channel for your question.",
                    delete_after=30,
                )
                await interaction.response.send_message(
                    f"You've already claimed {claimed_channel.mention}, please use that channel. If you need to change "
                    f"the topic ask a helper.",
                    ephemeral=True,
                )
                if claimed_channel.category.id == categories["help-archive"]:
                    await self.manager.update_archived_channel(claimed_channel, member)
                    await claimed_channel.purge(
                        after=datetime.now() - timedelta(days=1),
                        check=lambda msg: msg.author.bot
                        and "moved to the archive" in msg.content,
                    )
                return

        await interaction.message.edit(
            content="*Claiming channel for you, please standby*", embeds=[]
        )
        await self.manager.update_get_help_channel(
            interaction.channel, member, ticket.language, ticket.topics
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
