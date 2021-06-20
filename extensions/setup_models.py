import dippy
import dippy.labels
from discord import *


class SetupModelsExtension(dippy.Extension):
    labels: dippy.labels.storage.StorageInterface

    @dippy.Extension.listener("ready")
    async def on_ready(self):
        async def get_label(member: Member, label_name: str, default=None):
            return await self.labels.get(
                f"member[{member.guild.id}]", member.id, label_name, default
            )

        async def set_label(member: Member, label_name: str, value):
            await self.labels.set(
                f"member[{member.guild.id}]", member.id, label_name, value
            )

        def is_admin(member: Member):
            return member.guild_permissions.administrator

        Member.get_label = get_label
        Member.set_label = set_label
        Member.is_admin = is_admin

        async def get_label(guild: Guild, label_name: str, default=None):
            return await self.labels.get("guild", guild.id, label_name, default)

        async def set_label(guild: Guild, label_name: str, value):
            await self.labels.set(f"guild", guild.id, label_name, value)

        Guild.get_label = get_label
        Guild.set_label = set_label
