from discord import Message, utils
from extensions.help_channels.channel_manager import ChannelManager
import dippy.labels
import dippy.logging


class HelpRotatorCommandsExtension(dippy.Extension):
    client: dippy.client.Client
    log: dippy.logging.Logging
    labels: dippy.labels.storage.StorageInterface
    manager: ChannelManager

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

        helper = utils.get(message.guild.roles, name="helpers")
        owner = await self.labels.get("text_channel", message.channel.id, "owner")
        if helper not in message.author.roles and message.author.id != owner:
            return

        await self.manager.archive_channel(message.channel)

    @dippy.Extension.command("!topic")
    async def topic(self, message: Message):
        categories = await self.manager.get_categories(message.guild)
        if message.channel.category.id not in categories.values():
            return

        helpers = utils.get(message.guild.roles, name="helpers")
        if (
            helpers not in message.author.roles
            or await self.manager.get_owner(message.channel, True) != message.author.id
        ):
            return

        *_, topic = message.content.partition(" ")
        topic = self.manager.sluggify(topic)
        if not topic:
            await message.channel.send("You must provide a topic")
            return

        await self.manager.set_channel_topic(message.channel, topic)
