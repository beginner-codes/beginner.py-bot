from beginner.cog import Cog, commands
from beginner.colors import *
from beginner.models.points import Points
from beginner.scheduler import schedule, task_scheduled
from beginner.tags import tag
from datetime import datetime, timedelta
from time import time
import asyncio
import nextcord
import nextcord.ext.commands
import os
import peewee
import pytz


class BumpButton(nextcord.ui.View):
    @nextcord.ui.button(
        emoji="🔔", style=nextcord.ButtonStyle.blurple, custom_id="BumpButton"
    )
    async def button_pressed(self, _, interaction: nextcord.Interaction):
        guild = interaction.guild
        bump_role = nextcord.utils.get(guild.roles, name="Bumpers")
        if bump_role in interaction.user.roles:
            await interaction.user.remove_roles(bump_role)
            await interaction.response.send_message(
                f"{interaction.user.mention} you will no longer be tagged by bump reminders"
            )
            await asyncio.sleep(7)
            await interaction.delete_original_message()
        elif bump_role not in interaction.user.roles:
            await interaction.user.add_roles(bump_role)
            await interaction.response.send_message(
                f"{interaction.user.mention} you will be tagged by bump reminders"
            )
            await asyncio.sleep(7)
            await interaction.delete_original_message()


class Bumping(Cog):
    def __init__(self, client):
        super().__init__(client)
        self.bump_button_added = False

    @commands.Cog.listener()
    async def on_ready(self):
        if not self.bump_button_added:
            self.client.add_view(BumpButton(timeout=None))
            self.bump_button_added = True


def setup(client):
    client.add_cog(Bumping(client))
