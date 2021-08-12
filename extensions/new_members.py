from extensions.kudos.manager import KudosManager
from discord import Guild, Member, Message, TextChannel, utils
from typing import Optional
import dippy.labels
import dippy


class VoiceChatExtension(dippy.Extension):
    kudos: KudosManager
    labels: dippy.labels.storage.StorageInterface

    @dippy.Extension.command("!set welcome channel")
    async def set_welcome_channel(self, message: Message):
        if not message.author.guild_permissions.manage_channels:
            return

        await self.labels.set(
            "guild",
            message.guild.id,
            "welcome_channel_id",
            message.channel_mentions[0].id,
        )

    @dippy.Extension.listener("member_update")
    async def member_accepts_rules(self, before: Member, after: Member):
        if before.pending and not after.pending:
            await self.add_unwelcomed_user(after)

            last_highest = await self.labels.get(
                "guild", after.guild.id, "highest-member-count", default=0
            )
            count = self.get_num_members(after.guild)
            if count > last_highest:
                await self.labels.set(
                    "guild", after.guild.id, "highest-member-count", count
                )
                if count // 100 > last_highest // 100:
                    await after.guild.get_channel(644299524151443487).send(
                        f"🎉🥳🎈 We've reached {count // 100 * 100} members!!! 🎈🥳🎉"
                    )

    def get_num_members(self, guild: Guild) -> int:
        return sum(1 for member in guild.members if not member.bot)

    @dippy.Extension.listener("message")
    async def welcome_messages(self, message: Message):
        if message.author.bot or not isinstance(message.channel, TextChannel):
            return

        channel = await self.get_welcome_channel(message.guild)
        if message.channel != channel:
            return

        unwelcomed_members = await self.get_unwelcomed_users(message.guild)
        if not unwelcomed_members or message.author in unwelcomed_members:
            return

        await self._give_kudos_for_welcoming(
            message.author, len(unwelcomed_members), channel
        )

    async def get_welcome_channel(self, guild: Guild) -> Optional[TextChannel]:
        channel_id = await self.labels.get("guild", guild.id, "welcome_channel_id")
        return channel_id and guild.get_channel(channel_id)

    async def get_unwelcomed_users(self, guild: Guild) -> list[Member]:
        return [
            guild.get_member(member_id)
            for member_id in await self.labels.get(
                "guild", guild.id, "unwelcomed_members", []
            )
        ]

    async def add_unwelcomed_user(self, member: Member):
        unwelcomed = await self.get_unwelcomed_users(member.guild)
        unwelcomed.append(member)
        await self._set_unwelcomed_users(member.guild, unwelcomed)

    async def clear_unwelcomed_users(self, guild: Guild):
        await self._set_unwelcomed_users(guild, [])

    async def _give_kudos_for_welcoming(
        self, member: Member, num_welcomed: int, channel: TextChannel
    ):
        kudos = 2 * num_welcomed
        await self.clear_unwelcomed_users(member.guild)
        await self.kudos.give_kudos(
            member,
            kudos,
            f"{member.mention} welcomed {num_welcomed} member{'s' * (num_welcomed > 1)} to the server!!!",
        )
        expert_emoji = utils.get(member.guild.emojis, name="expert")
        await channel.send(
            f"{expert_emoji} {member.mention} you got {kudos} kudos for welcoming {num_welcomed} "
            f"member{'s' * (num_welcomed > 1)}!",
            delete_after=60,
        )

    async def _set_unwelcomed_users(self, guild: Guild, unwelcomed: list[Member]):
        await self.labels.set(
            "guild",
            guild.id,
            "unwelcomed_members",
            [member.id for member in unwelcomed],
        )
