from discord import Message
from extensions.help_channels.channel_manager import ChannelManager
import dippy.labels


class HelpRotatorExtension(dippy.Extension):
    client: dippy.client.Client
    log: dippy.logging.Logging
    labels: dippy.labels.storage.StorageInterface
    manager: ChannelManager

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
