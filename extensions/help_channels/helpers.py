from discord import Embed, Message, TextChannel
from extensions.help_channels.channel_manager import ChannelManager
import asyncio
import dippy.client
import nextcord.ui


class VolunteerHelperButtons(nextcord.ui.View):
    @nextcord.ui.button(
        emoji="🙋",
        label="Volunteer",
        style=nextcord.ButtonStyle.blurple,
        custom_id="volunteer_to_help",
    )
    async def volunteer_to_help(self, _, interaction: nextcord.Interaction):
        help_role = nextcord.utils.get(interaction.guild.roles, name="helpers")
        if help_role not in interaction.user.roles:
            await interaction.user.add_roles(help_role)
            await interaction.response.send_message(
                f"{interaction.user.mention} you are now a volunteer helper",
                ephemeral=True,
            )
            await asyncio.sleep(10)
            await interaction.delete_original_message()

    @nextcord.ui.button(
        emoji="🚫",
        label="Stop Helping",
        style=nextcord.ButtonStyle.grey,
        custom_id="stop_helping",
    )
    async def stop_helping(self, _, interaction: nextcord.Interaction):
        help_role = nextcord.utils.get(interaction.guild.roles, name="helpers")
        if help_role in interaction.user.roles:
            await interaction.user.remove_roles(help_role)
            await interaction.response.send_message(
                f"{interaction.user.mention} you are now no longer a volunteer helper",
                ephemeral=True,
            )
            await asyncio.sleep(10)
            await interaction.delete_original_message()


class HelpChannelModerationExtension(dippy.Extension):
    client: dippy.client.Client
    manager: ChannelManager

    @dippy.Extension.listener("ready")
    async def on_ready(self):
        self.client.add_view(VolunteerHelperButtons(timeout=None))

    @dippy.Extension.command("!setup volunteer helper message")
    async def setup_volunteer_helper_message(self, message: Message):
        if not message.author.guild_permissions.administrator:
            return

        channel: TextChannel = message.channel_mentions[0]
        await channel.send(
            embed=Embed(
                title="Volunteer To Help",
                description=(
                    "If you would like to be notified when members need help with their coding questions click the "
                    "button below."
                ),
                color=0x306998,
            ),
            view=VolunteerHelperButtons(timeout=None),
        )
