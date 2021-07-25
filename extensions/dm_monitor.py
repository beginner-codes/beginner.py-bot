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
        if (
            not isinstance(message.channel, discord.DMChannel)
            or message.author == self.client.user
        ):
            return

        channel = await self.get_logging_channel()
        await channel.send(
            embed=discord.Embed(
                title=f"New DM From @{message.author} ({message.author.id})",
                description=message.clean_content,
                color=0xFFE873,
            ).set_footer(f"Bound to DM message {message.author}")
        )
        await message.guild.set_label(
            "message-bind-target", ("member", message.author.id)
        )

        warned = await self.labels.get(
            "user", message.author.id, "dm-logging-channel-warning", default=False
        )
        if not warned:
            await message.channel.send(
                message.author.mention,
                embed=discord.Embed(
                    title="Hi!",
                    description=(
                        "Feel free to use my commands here in my DMs, I just want you to be aware that all messages are"
                        " monitored."
                    ),
                    color=0xFFE873,
                ).set_thumbnail(
                    url="https://cdn.discordapp.com/emojis/711749954837807135.png?v=1"
                ),
            )
            await self.labels.set(
                "user", message.author.id, "dm-logging-channel-warning", True
            )

    async def get_logging_channel(self) -> discord.TextChannel:
        if not self.log_channel:
            self.log_channel = self.client.get_channel(
                await self.labels.get("guild", -1, "dm-logging-channel")
            )
        return self.log_channel
