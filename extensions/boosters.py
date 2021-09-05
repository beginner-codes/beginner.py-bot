from datetime import datetime
from typing import Optional
import dippy.labels
import discord


class BoostersExtension(dippy.Extension):
    client: dippy.Client
    labels: dippy.labels.storage.StorageInterface

    async def get_booster_channel(
        self, guild: discord.Guild
    ) -> Optional[discord.TextChannel]:
        channel_id = await self.labels.get("guild", guild.id, "booster_channel_id")
        return channel_id and guild.get_channel(channel_id)

    @dippy.Extension.listener("member_update")
    async def archive_mod_chat_command(
        self, before: discord.Member, member: discord.Member
    ):
        if member.guild.premium_subscriber_role not in member.roles:
            return

        if member.guild.premium_subscriber_role in before.roles:
            return

        await self.send_booster_message(member)

    @dippy.Extension.command("!set booster channel")
    async def set_booster_channel_command(self, message: discord.Message):
        if message.author.guild_permissions.administrator:
            await self.labels.set(
                "guild",
                message.guild.id,
                "booster_channel_id",
                message.channel_mentions[0].id,
            )

    @dippy.Extension.command("!test booster channel")
    async def test_booster_channel_command(self, message: discord.Message):
        await self.send_booster_message(message.author, test=True)

    async def send_booster_message(self, member: discord.Member, *, test: bool = False):
        channel = await self.get_booster_channel(member.guild)
        await channel.send(
            embed=discord.Embed(
                description=(
                    f"{member.mention} has boosted the server! That's {member.guild.premium_subscription_count} "
                    f"boosts from {len(member.guild.premium_subscribers)} members!!!"
                ),
                color=0xFF65F9,
            )
            .set_author(
                name=f"{member} Has Boosted The Server!!!{' (TEST)' * test}",
                icon_url=member.avatar.url,
            )
            .set_thumbnail(
                url="https://raw.githubusercontent.com/beginnerpy-com/beginner.py-bot/dippy-rewrite/booster.png"
            )
        )
