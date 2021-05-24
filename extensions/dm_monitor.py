import dippy.labels
import dippy
import discord
import re


class DMMonitoringExtension(dippy.Extension):
    client: dippy.Client
    labels: dippy.labels.storage.StorageInterface

    def __init__(self):
        super().__init__()
        self.log_channel = None

    @dippy.Extension.command("!set dm logging channel")
    async def set_logging_channel(self, message: discord.Message):
        if not message.author.guild_permissions.kick_members:
            return

        channel_id, *_ = re.search(r"<#(\d+)>", message.content).groups()
        channel = message.guild.get_channel(int(channel_id))
        await self.labels.set("guild", -1, "dm-logging-channel", channel.id)
        self.log_channel = channel
        await channel.send("This channel is now monitoring DMs")

    @dippy.Extension.listener("message")
    async def on_message(self, message: discord.Message):
        if not isinstance(message.channel, discord.DMChannel):
            return

        channel = await self.get_logging_channel()
        await channel.send(
            embed=discord.Embed(
                title=f"New DM From @{message.author}",
                description=message.clean_content,
                color=0xFFE873,
            )
        )

    async def get_logging_channel(self) -> discord.TextChannel:
        if not self.log_channel:
            self.log_channel = self.client.get_channel(
                await self.labels.get("guild", -1, "dm-logging-channel")
            )
        return self.log_channel
