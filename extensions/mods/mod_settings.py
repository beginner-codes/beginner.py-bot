from dippy import Extension
from discord import Embed, Guild, Message, Role, TextChannel
from typing import Optional


class ModSettingsExtension(Extension):
    def __init__(self):
        super().__init__()
        self._mod_roles: Optional[Role] = None
        self._helper_roles: Optional[Role] = None
        self._mute_role: Optional[Role] = None
        self._suspend_role: Optional[Role] = None
        self._mod_log_channel: Optional[TextChannel] = None
        self._mod_channel: Optional[TextChannel] = None

    @Extension.command("!mod settings")
    async def show_mod_settings_command(self, message: Message):
        mute_role = await self.get_mute_role(message.guild)
        suspend_role = await self.get_suspend_role(message.guild)
        mod_log_channel = await self.get_mod_log_channel(message.guild)
        mod_channel = await self.get_mod_channel(message.guild)
        await message.channel.send(
            embed=(
                Embed(
                    title="Mod Settings", description="Here are all the mod settings."
                )
                .add_field(
                    name="Mod Roles",
                    value=", ".join(
                        role.mention for role in await self.get_mod_roles(message.guild)
                    )
                    or "*No Helper Roles Set*",
                    inline=False,
                )
                .add_field(
                    name="Helper Roles",
                    value=", ".join(
                        role.mention
                        for role in await self.get_helper_roles(message.guild)
                    )
                    or "*No Mod Roles Set*",
                    inline=False,
                )
                .add_field(
                    name="Moderation Status Roles",
                    value=(
                        f"Mute Role: {mute_role and mute_role.mention or '*No Mute Role Set*'}\n"
                        f"Suspend Role: {suspend_role and suspend_role.mention or '*No Suspend Role Set*'}"
                    ),
                    inline=False,
                )
                .add_field(
                    name="Mod Channels",
                    value=(
                        f"Mod Log Channel: {mod_log_channel and mod_log_channel.mention or '*No Mod Log Channel Set*'}\n"
                        f"Mod Channel: {mod_channel and mod_channel.mention or '*No Mod Channel Set*'}\n"
                    ),
                    inline=False,
                )
            )
        )

    @Extension.command("!add mod role")
    async def add_mod_role_command(self, message: Message):
        if not message.author.is_admin():
            return

        role_ids = await message.guild.get_label("mod_role_ids", set())
        for role in message.role_mentions:
            role_ids.add(role.id)

        self._mod_roles = None
        await message.guild.set_label("mod_role_ids", role_ids)
        await message.channel.send("Added roles as moderators")

    @Extension.command("!remove mod role")
    async def remove_mod_role_command(self, message: Message):
        if not message.author.is_admin():
            return

        role_ids = await message.guild.get_label("mod_role_ids", set())
        for role in message.role_mentions:
            role_ids.remove(role.id)

        self._mod_roles = None
        await message.guild.set_label("mod_role_ids", role_ids)
        await message.channel.send("Removed roles as moderators")

    @Extension.command("!add staff role")
    async def add_helper_role_command(self, message: Message):
        if not message.author.is_admin():
            return

        role_ids = await message.guild.get_label("helper_role_ids", set())
        for role in message.role_mentions:
            role_ids.add(role.id)

        self._helper_roles = None
        await message.guild.set_label("helper_role_ids", role_ids)
        await message.channel.send("Added roles as staff")

    @Extension.command("!remove staff role")
    async def remove_staff_role_command(self, message: Message):
        if not message.author.is_admin():
            return

        role_ids = await message.guild.get_label("helper_role_ids", set())
        for role in message.role_mentions:
            role_ids.remove(role.id)

        self._helper_roles = None
        await message.guild.set_label("helper_role_ids", role_ids)
        await message.channel.send("Removed roles as staff")

    @Extension.command("!set mute role")
    async def set_mute_role_command(self, message: Message):
        if not message.author.is_admin():
            return

        role_id = None
        if message.role_mentions:
            role_id = message.role_mentions[0].id

        self._mute_role = None
        await message.guild.set_label("mute_role_id", role_id)
        await message.channel.send(
            "Set the mute role" if role_id else "Removed the mute role"
        )

    @Extension.command("!set suspend role")
    async def set_suspend_role_command(self, message: Message):
        if not message.author.is_admin():
            return

        role_id = None
        if message.role_mentions:
            role_id = message.role_mentions[0].id

        self._suspend_role = None
        await message.guild.set_label("suspend_role_id", role_id)
        await message.channel.send(
            "Set the suspend role" if role_id else "Removed the suspend role"
        )

    @Extension.command("!set mod log channel")
    async def set_mod_log_channel_command(self, message: Message):
        if not message.author.is_admin():
            return

        channel_id = None
        if message.channel_mentions:
            channel_id = message.channel_mentions[0].id

        self._mod_log_channel = None
        await message.guild.set_label("mod_log_channel_id", channel_id)
        await message.channel.send(
            "Set the mod log channel" if channel_id else "Removed the mod log channel"
        )

    @Extension.command("!set mod channel")
    async def set_mod_channel_command(self, message: Message):
        if not message.author.is_admin():
            return

        channel_id = None
        if message.channel_mentions:
            channel_id = message.channel_mentions[0].id

        self._mod_channel = None
        await message.guild.set_label("mod_channel_id", channel_id)
        await message.channel.send(
            "Set the mod channel" if channel_id else "Removed the mod channel"
        )

    async def get_mod_roles(self, guild: Guild) -> set[Role]:
        if self._mod_roles is None:
            self._mod_roles = {
                role
                for role_id in await guild.get_label("mod_role_ids", set())
                if (role := guild.get_role(role_id))
            }
        return self._mod_roles

    async def get_helper_roles(self, guild: Guild) -> set[Role]:
        if self._helper_roles is None:
            self._helper_roles = {
                role
                for role_id in await guild.get_label("helper_role_ids", set())
                if (role := guild.get_role(role_id))
            }
        return self._helper_roles

    async def get_mute_role(self, guild: Guild) -> Optional[Role]:
        if self._mute_role is None:
            role_id = await guild.get_label("mute_role_id")
            self._mute_role = role_id and guild.get_role(role_id)

        return self._mute_role

    async def get_suspend_role(self, guild: Guild) -> Optional[Role]:
        if self._suspend_role is None:
            role_id = await guild.get_label("suspend_role_id")
            self._suspend_role = role_id and guild.get_role(role_id)

        return self._suspend_role

    async def get_mod_log_channel(self, guild: Guild) -> Optional[TextChannel]:
        if self._mod_log_channel is None:
            channel_id = await guild.get_label("mod_log_channel_id")
            self._mod_log_channel = channel_id and guild.get_channel(channel_id)

        return self._mod_log_channel

    async def get_mod_channel(self, guild: Guild) -> Optional[TextChannel]:
        if self._mod_channel is None:
            channel_id = await guild.get_label("mod_channel_id")
            self._mod_channel = channel_id and guild.get_channel(channel_id)

        return self._mod_channel
