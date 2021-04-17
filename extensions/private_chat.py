from datetime import datetime
import asyncio
import dippy
import dippy.labels
import discord


class PrivateChatExtension(dippy.Extension):
    client: dippy.Client
    log: dippy.logging.Logging
    labels: dippy.labels.storage.StorageInterface

    @dippy.Extension.command("!archive")
    async def archive_mod_chat_command(self, message: discord.Message):
        if not message.author.guild_permissions.kick_members:
            return

        category = await self.get_mod_chat_category(message.guild)
        if not category or message.channel.category != category:
            return

        message.channel: discord.TextChannel = message.channel
        await message.channel.edit(
            name=f"{message.channel.name}-archive", sync_permissions=True
        )
        await message.channel.send("🗂 This channel has been archived")

    @dippy.Extension.command("!close")
    async def close_mod_chat_command(self, message: discord.Message):
        if not message.author.guild_permissions.kick_members:
            return

        category = await self.get_mod_chat_category(message.guild)
        if not category or message.channel.category != category:
            return

        await message.channel.delete()

    @dippy.Extension.command("!modchat")
    async def mod_chat_command(self, message: discord.Message):
        if not message.author.guild_permissions.kick_members:
            return

        category = await self.get_mod_chat_category(message.guild)
        if not category:
            return

        date = datetime.utcnow().strftime("%d%m%Y")
        overwrites = category.overwrites.copy()
        for member in message.mentions:
            overwrites[member] = discord.PermissionOverwrite(read_messages=True)
        channel = await category.create_text_channel(name=date, overwrites=overwrites)
        mentions = ", ".join(member.mention for member in message.mentions)
        await channel.send(
            f"{mentions} you can discuss privately with the mod team here."
        )

    @dippy.Extension.command("!set modchat category")
    async def set_mod_chat_category_command(self, message: discord.Message):
        if not message.author.guild_permissions.administrator:
            return

        category_name = message.content.removeprefix("!set modchat category ").strip()
        guild: discord.Guild = message.guild
        category = discord.utils.get(guild.categories, name=category_name)

        if not category:
            await message.channel.send(
                f"Couldn't find a category named {category_name!r}"
            )
            return

        await self.set_mod_chat_category(guild, category)
        await message.channel.send(
            f"Set {category_name} as the modchat category for {guild.name}"
        )

    async def get_mod_chat_category(
        self, guild: discord.Guild
    ) -> discord.CategoryChannel:
        return guild.get_channel(
            await self.labels.get("guild", guild.id, "mod-chat-category")
        )

    async def set_mod_chat_category(
        self, guild: discord.Guild, category: discord.CategoryChannel
    ) -> discord.CategoryChannel:
        await self.labels.set("guild", guild.id, "mod-chat-category", category.id)
