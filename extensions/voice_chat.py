from datetime import datetime, timedelta
from discord import Member, PermissionOverwrite, VoiceChannel, VoiceState, utils
from extensions.kudos.manager import KudosManager
import asyncio
import dippy
import dippy.labels


class VoiceChatExtension(dippy.Extension):
    client: dippy.Client
    kudos: KudosManager
    labels: dippy.labels.storage.StorageInterface

    @dippy.Extension.listener("ready")
    async def on_ready(self):
        permissions = self.get_voice_chat_perms()
        if permissions.stream and not self.get_num_mods():
            last_mod_time = await self.labels.get(
                "guild", 644299523686006834, "last-mod-in-vc"
            )
            if not last_mod_time or datetime.utcnow() - datetime.fromisoformat(
                last_mod_time
            ) > timedelta(minutes=1):
                await self.disable_streaming()
            else:
                await asyncio.sleep(
                    (
                        (datetime.fromisoformat(last_mod_time) + timedelta(minutes=1))
                        - datetime.utcnow()
                    ).total_seconds()
                )
                if not self.get_num_mods():
                    await self.disable_streaming()

    @dippy.Extension.listener("voice_state_update")
    async def manage_dj_role(
        self, member: Member, before: VoiceState, after: VoiceState
    ):
        role = utils.get(member.guild.roles, name="🎸Music DJ🎸")
        has_role = role in member.roles
        if has_role and after.channel is None:
            await member.remove_roles(role)
        elif (
            not has_role
            and after.channel
            and await self.kudos.has_achievement(member, "MUSIC_DJ")
        ):
            await member.add_roles(role)

    @dippy.Extension.listener("voice_state_update")
    async def manage_streaming_permissions(
        self, member: Member, before: VoiceState, after: VoiceState
    ):
        if not self.is_voice_mod(member):
            return

        perms = self.get_voice_chat_perms()
        num_mods = self.get_num_mods()
        if num_mods:
            changed = await self.enable_streaming()
            status = "🟢 enabled"
        elif perms.stream:
            await self.labels.set(
                "guild",
                644299523686006834,
                "last-mod-in-vc",
                datetime.utcnow().isoformat(),
            )
            if not self.get_num_mods():
                await self.client.get_channel(644828412405481492).send(
                    "🟡 If a mod or helper doesn't rejoin voice chat, video streaming will be disabled."
                )
            await asyncio.sleep(60)
            if not self.get_num_mods():
                changed = await self.disable_streaming()
                status = "🔴 disabled"

        if changed:
            await self.client.get_channel(644828412405481492).send(
                f"Video streaming has been {status} in {self.client.get_channel(702221517697581086).mention}"
            )

    async def disable_streaming(self) -> bool:
        channel: VoiceChannel = self.client.get_channel(702221517697581086)
        everyone = utils.get(channel.guild.roles, name="@everyone")
        overwrites: PermissionOverwrite = channel.overwrites_for(everyone)

        if overwrites.stream:
            updated = channel.overwrites.copy()
            overwrites.update(stream=False)
            updated[everyone] = overwrites
            await channel.edit(reason="Disabling streaming", overwrites=updated)
            return True
        return False

    async def enable_streaming(self) -> bool:
        channel: VoiceChannel = self.client.get_channel(702221517697581086)
        everyone = utils.get(channel.guild.roles, name="@everyone")
        overwrites: PermissionOverwrite = channel.overwrites_for(everyone)
        if not overwrites.stream:
            updated = channel.overwrites.copy()
            overwrites.update(stream=True)
            updated[everyone] = overwrites
            await channel.edit(reason="Enabling streaming", overwrites=updated)
            return True
        return False

    def get_num_mods(self) -> int:
        channel: VoiceChannel = self.client.get_channel(702221517697581086)
        return sum(self.is_voice_mod(member) for member in channel.members)

    def is_voice_mod(self, member: Member) -> bool:
        staff_role = utils.get(member.guild.roles, name="staff")
        mods_role = utils.get(member.guild.roles, name="mods")
        return staff_role in member.roles or mods_role in member.roles

    def get_voice_chat_perms(self) -> PermissionOverwrite:
        channel: VoiceChannel = self.client.get_channel(702221517697581086)
        everyone = utils.get(channel.guild.roles, name="@everyone")
        return channel.overwrites_for(everyone)
