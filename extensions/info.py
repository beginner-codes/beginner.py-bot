from discord import Embed, Message
import dippy


class InfoExtension(dippy.Extension):
    client: dippy.Client

    @dippy.Extension.listener("message")
    async def manage_streaming_permissions(
        self, message: Message
    ):
        if not message.guild:
            await message.channel.send("This command can only be used in a guild channel")
            return

        role = message.guild.default_role
        num_channels = len(message.guild.channels)
        num_visible_channels = sum(channel.permissions_for(role).view_channel for channel in message.guild.channels)

        await message.channel.send(
            embed=Embed(
                title="Total Channels",
                description=f"There are {num_channels} totals channels\n{num_visible_channels} are visible to @everyone"
            )
        )

