from discord import Message, utils
from extensions.help_channels.channel_manager import ChannelManager
import dippy.labels
import dippy.logging
import time


class HelpRotatorCommandsExtension(dippy.Extension):
    client: dippy.client.Client
    log: dippy.logging.Logging
    labels: dippy.labels.storage.StorageInterface
    manager: ChannelManager

    def __init__(self, *args):
        super().__init__(*args)
        self._topic_limit = 0

    @dippy.Extension.command("!done")
    async def done(self, message: Message):
        category = message.channel.category
        if not category or not category.guild:
            return

        if message.author.bot:
            return

        categories = await self.manager.get_categories(category.guild)
        if not categories:
            return

        if category.id != categories["getting-help"]:
            return

        lock = (
            message.author.guild_permissions.kick_members
            and "lock" in message.content.casefold()
        )

        helper = utils.get(message.guild.roles, name="helpers")
        owner = await self.labels.get("text_channel", message.channel.id, "owner")
        if helper not in message.author.roles and message.author.id != owner:
            return

        await self.manager.archive_channel(message.channel, remove_owner=lock)

    @dippy.Extension.listener("message")
    async def on_message(self, message: Message):
        if "!free" in message.content:
            categories = await self.manager.get_categories(message.guild)
            category = message.guild.get_channel(categories["get-help"])
            channel = category.channels[-1]
            await message.channel.send(
                f"You can claim {channel.mention} to ask your question."
            )

    @dippy.Extension.command("!topic")
    async def topic(self, message: Message):
        if time.time() - self._topic_limit < 120:
            await message.channel.send(
                f"Please wait {120 - int(time.time() - self._topic_limit)} seconds to set the topic."
            )
            return

        categories = await self.manager.get_categories(message.guild)
        if message.channel.category.id not in categories.values():
            return

        helpers = utils.get(message.guild.roles, name="helpers")
        if helpers not in message.author.roles:
            return

        *_, topic = message.content.partition(" ")
        topic = self.manager.sluggify(topic)
        if not topic:
            await message.channel.send("You must provide a topic")
            return

        self._topic_limit = time.time()
        await self.manager.set_channel_topic(message.channel, topic)
