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
