from discord import CategoryChannel, Guild, Message, TextChannel, utils
from extensions.help_channels.channel_manager import ChannelManager
import dippy.labels
import re


class HelpRotatorAdminExtension(dippy.Extension):
    client: dippy.client.Client
    log: dippy.logging.Logging
    labels: dippy.labels.storage.StorageInterface
    manager: ChannelManager

    @dippy.Extension.command("!setup help")
    async def setup_help(self, message: Message):
        if not message.author.guild_permissions.administrator:
            return

        try:
            content = message.content.removeprefix("!setup help").strip()
            categories = re.match(r"\s*([^,]+)[\s,]*([^,]+)[\s,]*(.+)", content).groups(
                ""
            )

            success = await self._label_categories(tuple(categories), message.channel)
            if not success:
                return

            await self._create_help_channels(message.guild)
            await message.channel.send("Setup the help channels.")
        except Exception as e:
            self.log.error(f"There was an error: {e.args}")
            await message.channel.send("Ooops something went wrong")
            raise

    @dippy.Extension.command("!get help info")
    async def get_help_info(self, message: Message):
        if not message.author.guild_permissions.administrator:
            return

        try:
            categories = await self.manager.get_categories(message.guild)
            names = {
                "help-archive": "Help Archive",
                "getting-help": "Getting Help",
                "get-help": "Get Help",
            }
            content = []
            for help_type, category_id in categories.items():
                category = self.client.get_channel(category_id)
                if help_type in names:
                    content.append(f"{names[help_type]}: {category.mention}")

            await message.channel.send("**Help Categories**\n" + "\n".join(content))
        except Exception:
            await message.channel.send("Ooops something went wrong")
            raise

    async def _label_categories(
        self, category_names: tuple[str], channel: TextChannel
    ) -> bool:
        categories = {}
        for category_name, help_type in zip(
            category_names, ("get-help", "getting-help", "help-archive")
        ):
            category: CategoryChannel = utils.get(
                channel.guild.categories, name=category_name
            )
            if not category:
                await channel.send(
                    f"Could not find a category with the name {category_name!r}"
                )
                return False

            categories[help_type] = category.id

        await self.manager.set_categories(channel.guild, categories)
        return True

    async def _create_help_channels(self, guild: Guild):
        help_categories: dict[str, int] = await self.manager.get_categories(guild)
        get_help_category: CategoryChannel = self.client.get_channel(
            help_categories["get-help"]
        )
        for i in range(4):
            await self.manager.create_help_channel(get_help_category, i > 1)
