from datetime import datetime
from discord import (
    CategoryChannel,
    Embed,
    Guild,
    Member,
    Message,
    PermissionOverwrite,
    TextChannel,
    utils,
)
from typing import Any, Optional
import ast
import dippy.labels
import dippy.client
import dippy.logging
import re


class HelpRotatorExtension(dippy.Extension):
    client: dippy.client.Client
    log: dippy.logging.Logging
    labels: dippy.labels.storage.StorageInterface

    @dippy.Extension.listener("message")
    async def on_message(self, message: Message):
        category = message.channel.category
        if not category or not category.guild:
            return

        if message.author.bot:
            return

        if message.content.startswith("!"):
            return

        categories = await self._get_guild_label(category.guild, "help-categories")
        if not categories:
            return

        for help_type, category_id in categories.items():
            if category.id != category_id:
                continue

            if help_type == "help-archive":
                await self._update_archived_channel(message.channel, message.author)
            elif help_type == "getting-help":
                await self._update_help_channel(message.channel, message.author)
            elif help_type == "get-help":
                await self._update_get_help_channel(message.channel, message.author)

    @dippy.Extension.command("!done")
    async def done(self, message: Message):
        category = message.channel.category
        if not category or not category.guild:
            return

        if message.author.bot:
            return

        categories = await self._get_guild_label(category.guild, "help-categories")
        if not categories:
            return

        if category.id != categories["getting-help"]:
            return

        helper = utils.get(message.guild.roles, name="helpers")
        owner = await self.labels.get("text_channel", message.channel.id, "owner")
        if helper not in message.author.roles and message.author.id != owner:
            return

        coders = utils.get(message.guild.roles, name="coders")
        await message.channel.edit(
            category=message.guild.get_channel(categories["help-archive"]),
            overwrites={
                message.author: PermissionOverwrite(send_messages=True),
                coders: PermissionOverwrite(send_messages=False),
            },
        )

        beginner = utils.get(self.client.emojis, name="beginner")
        intermediate = utils.get(self.client.emojis, name="intermediate")
        expert = utils.get(self.client.emojis, name="expert")
        await message.channel.send(
            f"{(await message.guild.fetch_member(owner)).mention} This channel has been moved to the archive.\n\nDon't forget "
            f"to give some kudos to show your appreciation by reacting with {beginner}, {intermediate}, or {expert}!"
        )

    @dippy.Extension.command("!setup help")
    async def setup_help(self, message: Message):
        if not message.author.guild_permissions.administrator:
            return

        try:
            content = message.content.removeprefix("!setup help").strip()
            categories = re.match(r"\s*([^,]+)[\s,]*([^,]+)[\s,]*(.+)", content).groups(
                ""
            )

            success = await self._label_categories(categories, message.channel)
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
            categories = await self._get_guild_label(message.guild, "help-categories")
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
        except:
            await message.channel.send("Ooops something went wrong")
            raise

    async def _get_guild_label(self, guild: Guild, label: str) -> Any:
        return await self.labels.get("guild", guild.id, label)

    async def _set_guild_label(self, guild: Guild, label: str, value: Any):
        await self.labels.set("guild", guild.id, label, value)

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

        await self._set_guild_label(channel.guild, "help-categories", categories)
        return True

    async def _create_help_channels(self, guild: Guild):
        help_categories: dict[str, int] = await self._get_guild_label(
            guild, "help-categories"
        )
        get_help_category: CategoryChannel = self.client.get_channel(
            help_categories["get-help"]
        )
        for i in range(4):
            await self._create_help_channel(get_help_category, i > 1)

    async def _create_help_channel(
        self, category: CategoryChannel, hidden: bool = True
    ):
        overwrites = {}
        if hidden:
            coders = utils.get(category.guild.roles, name="coders")
            overwrites[coders] = PermissionOverwrite(read_messages=False)

        channel = await category.create_text_channel(
            name=f"🙋get-help{'-hidden' if hidden else ''}", overwrites=overwrites
        )
        await channel.send(
            embed=Embed(
                title="Get Help Here",
                description=(
                    "To get help just ask your question (provide plenty of details) here. That will claim this channel "
                    "just for you. __When someone has a chance they will come by to help you.__\n\n*Once the channel "
                    "is claimed it will be moved so others won't ask questions in it.*"
                ),
                color=0x00FF66,
            )
        )

    async def _update_archived_channel(self, channel: TextChannel, author: Member):
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
        await self._update_help_channel(channel, author)

    async def _update_help_channel(self, channel: TextChannel, author: Member):
        owner = await self.labels.get(
            "text_channel", channel.id, "owner", default=author.id
        )
        if owner == author.id:
            last_active = datetime.fromisoformat(
                await self.labels.get(
                    "text_channel", channel.category.channels[0].id, "last-active"
                )
            )
            await self.labels.set(
                "text_channel", channel.id, "last-active", datetime.utcnow().isoformat()
            )
            if (
                channel.category.channels[0] != channel
                and (datetime.utcnow() - last_active).total_seconds() > 15
            ):
                await channel.edit(position=channel.category.channels[0].position)

    async def _update_get_help_channel(
        self, channel: TextChannel, owner: Member, topic: Optional[str] = None
    ):
        await self.labels.set("text_channel", channel.id, "owner", owner.id)
        await self.labels.set(
            "text_channel", channel.id, "last-active", datetime.utcnow().isoformat()
        )

        categories = await self._get_guild_label(channel.guild, "help-categories")

        name = f"helping-{owner.display_name}"
        if topic and (slug := self._sluggify(topic)):
            name = f"{name}-{slug}"

        helping_category = self.client.get_channel(categories["getting-help"])
        await channel.edit(
            reason=f"Claimed by {owner.display_name} for a question",
            name=name,
            category=helping_category,
            position=helping_category.channels[0].position,
        )

        help_category: CategoryChannel = self.client.get_channel(categories["get-help"])
        await help_category.channels[-2].edit(
            sync_permissions=True,
            name=help_category.channels[-2].name.removesuffix("-hidden"),
        )

        await self._create_help_channel(help_category, hidden=True)

    def _sluggify(self, text: str) -> str:
        parts = re.findall(r"[\w\d]", text)
        return "-".join(parts)
