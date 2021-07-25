from discord import AllowedMentions, Guild, Member, Message
import dippy.labels
import dippy


class DMBindingExtension(dippy.Extension):
    client: dippy.Client
    labels: dippy.labels.storage.StorageInterface

    @dippy.Extension.command("!!!")
    async def on_message(self, message: Message):
        content = message.content[3:]
        if not content:
            return

        channel_id = await message.guild.get_label("message-binding-channel-id")
        if message.channel.id != channel_id:
            return

        if not message.author.guild_permissions.ban_members:
            return

        success = await self.send(content, message.guild, message.author)
        await message.add_reaction("📤" if success else "❌")

    @dippy.Extension.command("!bind")
    async def bind_command(self, message: Message):
        if not message.author.guild_permissions.ban_members:
            return

        if message.mentions:
            await message.guild.set_label(
                "message-bind-target", ("member", message.mentions[0].id)
            )

        elif message.channel_mentions:
            await message.guild.set_label(
                "message-bind-target", ("channel", message.channel_mentions[0].id)
            )

        else:
            await message.channel.send(
                "You must mention a user or channel", message.guild
            )

    @dippy.Extension.command("!set binding channel")
    async def set_binding_channel_command(self, message: Message):
        if not message.author.guild_permissions.administrator:
            return

        await message.guild.set_label(
            "message-binding-channel-id", message.channel_mentions[0].id
        )

    async def send(self, message: str, guild: Guild, from_member: Member) -> bool:
        bind_type, bind_id = await guild.get_label("message-bind-target")
        channel = (
            guild.get_channel(bind_id)
            if bind_type == "channel"
            else guild.get_member(bind_id)
        )

        if not channel:
            return False

        await channel.send(
            f"{message}\n\n*From {from_member}",
            allowed_mentions=AllowedMentions(everyone=False, roles=False),
        )

        channel_id = await message.guild.get_label("message-binding-channel-id")
        await guild.get_channel(channel_id).send(
            f"Sent to {channel.mention}", delete_after=2
        )
        return True
