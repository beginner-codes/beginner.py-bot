from bevy import Injectable, Factory
from discord import Embed, Message, TextChannel
from extensions.help_channels.channel_manager import ChannelManager
from extensions.kudos.manager import KudosManager
import asyncio
import dippy.client
import nextcord.ui


class VolunteerHelperButtons(nextcord.ui.View, Injectable):
    kudos: KudosManager

    def __init__(self):
        super().__init__(timeout=None)

    @nextcord.ui.button(
        emoji="🙋",
        label="Volunteer",
        style=nextcord.ButtonStyle.blurple,
        custom_id="volunteer_to_help",
    )
    async def volunteer_to_help(self, _, interaction: nextcord.Interaction):
        help_role = nextcord.utils.get(interaction.guild.roles, name="helpers")
        if help_role in interaction.user.roles:
            return

        kudos = await self.kudos.get_lifetime_kudos(
            interaction.guild.get_member(interaction.user.id)
        )
        if kudos < 75:
            await interaction.response.send_message(
                f"{interaction.user.mention} you must have 75 kudos to volunteer",
                ephemeral=True,
            )
            return

        await interaction.user.add_roles(help_role)
        await interaction.response.send_message(
            f"{interaction.user.mention} you are now a volunteer helper",
            ephemeral=True,
        )

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


class HelpChannelModerationExtension(dippy.Extension):
    client: dippy.client.Client
    manager: ChannelManager
    helper_button_factory: Factory[VolunteerHelperButtons]

    @dippy.Extension.listener("ready")
    async def on_ready(self):
        self.client.add_view(self.helper_button_factory())

    @dippy.Extension.command("!setup volunteer helper message")
    async def setup_volunteer_helper_message(self, message: Message):
        if not message.author.guild_permissions.administrator:
            return

        channel: TextChannel = message.channel_mentions[0]
        expert_emoji = nextcord.utils.get(message.guild.emojis, name="expert")
        await channel.send(
            embed=Embed(
                title="Volunteer To Help",
                description=(
                    f"If you would like to be notified when members need help with their coding questions click the "
                    f"button below. __You must have 75 kudos to volunteer.__ Helpers receive 2x kudos {expert_emoji} in "
                    f"help channels."
                ),
                color=0x306998,
            ),
            view=self.helper_button_factory(),
        )
