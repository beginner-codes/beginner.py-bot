from extensions.kudos.manager import KudosManager
from discord import Member, VoiceState, utils
import dippy


class VoiceChatExtension(dippy.Extension):
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
