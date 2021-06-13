from extensions.kudos.manager import KudosManager
from discord import Member, PermissionOverwrite, VoiceChannel, VoiceState, utils
import dippy


class VoiceChatExtension(dippy.Extension):
    client: dippy.Client
    kudos: KudosManager

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
        channel_id = before.channel and before.channel.id or after.channel.id
        if channel_id != 702221517697581086:
            return

        if not self.is_voice_mod(member):
            return

        num_mods = self.get_num_mods()
        if num_mods:
            changed = await self.enable_streaming()
            status = "enabled"
        else:
            changed = await self.disable_streaming()
            status = "disabled"

        if changed:
            await self.client.get_channel(644828412405481492).send(
                f"Video streaming has been {status} in {self.client.get_channel(channel_id).mention}"
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
        helpers_role = utils.get(member.guild.roles, name="helpers")
        mods_role = utils.get(member.guild.roles, name="mods")
        return helpers_role in member.roles or mods_role in member.roles
