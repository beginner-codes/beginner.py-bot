from nextcord import Guild, Member, Message, Status, TextChannel
from datetime import datetime, timedelta
import dippy


class OnlineCounterExtension(dippy.Extension):
    client: dippy.Client

    @dippy.Extension.listener("presence_update")
    async def on_presence_update(self, _, member: Member):
        num_online = self._count_online_members(member.guild)
        max_online = await member.guild.get_label("max_online", default=0)
        if num_online > max_online:
            self._update_max_online(member.guild, num_online)
            await self._broadcast_new_record(member.guild, num_online)

    @dippy.Extension.command("!set max online channel")
    async def set_max_online_broadcast_channel(self, message: Message):
        if not message.author.guild_permissions.administrator or message.author.bot:
            return

        await self._set_broadcast_channel(message.channel_mentions[0])
        await message.channel.send(
            f"Max online broadcast channel is set to {message.channel_mentions[0]}"
        )

    async def _broadcast_new_record(self, guild: Guild, num_online: int):
        if await self._should_broadcast(guild):
            channel = await self._get_broadcast_channel(guild)
            await channel.send(
                f"We've just broken the record for most members online! There are now {num_online} members online!!!"
            )
            await self._did_broadcast(guild)

    def _count_online_members(self, guild: Guild) -> int:
        return sum(member.status != Status.offline for member in guild.members)

    async def _did_broadcast(self, guild: Guild):
        await guild.set_label(
            "last_max_online_broadcast", datetime.utcnow().isoformat()
        )

    async def _get_broadcast_channel(self, guild: Guild) -> TextChannel:
        channel_id = await guild.get_label("max_online_broadcast_channel_id")
        return guild.get_channel(channel_id)

    async def _set_broadcast_channel(self, channel: TextChannel):
        await channel.guild.set_label("max_online_broadcast_channel_id", channel.id)

    async def _should_broadcast(self, guild: Guild) -> bool:
        last_broadcast_iso = await guild.get_label(
            "last_max_online_broadcast", datetime.fromtimestamp(0).isoformat()
        )
        last_broadcast = datetime.fromisoformat(last_broadcast_iso)
        return datetime.utcnow() - last_broadcast > timedelta(minutes=30)

    def _update_max_online(self, guild: Guild, num_online: int):
        await guild.set_label("max_online", num_online)
