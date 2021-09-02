from beginner.cog import Cog
from beginner.colors import *
from beginner.scheduler import schedule
from beginner.tags import tag
import asyncio
import datetime
import nextcord
import nextcord.ext.commands


class HelpRotatorCog(Cog):
    def __init__(self, client):
        super().__init__(client)
        self.rotation_lock = asyncio.Lock()
        self.available_channel_ids = []

    async def ready(self):
        self.available_channel_ids = [
            channel.id
            for channel in self.server.channels
            if channel.category_id == self.available_category.id
        ]

    @property
    def available_category(self) -> nextcord.CategoryChannel:
        return self.get_category("Help: Available")

    @property
    def occupied_category(self) -> nextcord.CategoryChannel:
        return self.get_category("Help: Occupied")

    @Cog.listener()
    async def on_message(self, message: nextcord.Message):
        if message.author.bot:
            return

        if self.is_available_python_help_channel(message.channel):
            await self.rotate_available_channels(message)
        elif self.is_occupied_python_help_channel(message.channel):
            await self.rotate_occupied_channels(message)

    @Cog.command("remind", aliases=["remind-me", "remindme"])
    async def remind(
        self, ctx: nextcord.ext.commands.Context, duration: str, *, message: str
    ):
        minutes = 0
        hours = 0
        days = 0
        if duration.casefold().endswith("d"):
            days = int(duration[:-1])
        elif duration.casefold().endswith("h"):
            hours = int(duration[:-1])
        elif duration.casefold().endswith("m"):
            minutes = int(duration[:-1])
        elif duration.isdigit():
            minutes = int(duration)
        else:
            await ctx.send(
                f"{ctx.author.mention} durations must be of the format `123d`, `123h`, or `123m`/`123`.",
                delete_after=15,
            )
            return

        if minutes < 1 and hours < 1 and days < 1:
            await ctx.send(
                f"{ctx.author.mention} cannot set a reminder for less than a minute",
                delete_after=15,
            )
            return

        time_duration = datetime.timedelta(days=days, hours=hours, minutes=minutes)
        scheduled = schedule(
            f"reminder-{ctx.author.id}",
            time_duration,
            self.reminder_handler,
            message,
            ctx.message.id,
            ctx.channel.id,
        )
        if scheduled:
            await ctx.send(
                f"{ctx.author.mention} a reminder has been set", delete_after=15
            )
        else:
            await ctx.send(
                f"{ctx.author.mention} you already have a reminder scheduled",
                delete_after=15,
            )

    @tag("schedule", "reminder")
    async def reminder_handler(self, content: str, message_id: int, channel_id: int):
        channel: nextcord.TextChannel = self.server.get_channel(channel_id)
        message: nextcord.Message = await channel.fetch_message(message_id)
        author: nextcord.Member = message.author
        await channel.send(
            content=f"{author.mention}",
            embed=nextcord.Embed(description=content, color=BLUE).set_author(
                name="Reminder ⏰"
            ),
        )

    async def rotate_available_channels(self, message: nextcord.Message):
        channel: nextcord.TextChannel = message.channel
        if channel.id not in self.available_channel_ids:
            return

        self.available_channel_ids.remove(channel.id)

        # Rotate next occupied channel into active
        next_channel = self.get_next_channel()
        await next_channel.send(
            embed=nextcord.Embed(
                description="Feel free to ask any of your Python related questions in this channel!",
                color=GREEN,
            ).set_author(
                name="This Channel Is Available", icon_url=self.server.icon_url
            )
        )

        async with self.rotation_lock:
            current_bottom_available = self.available_category.channels[-1].position
            await next_channel.edit(
                category=self.available_category,
                position=current_bottom_available,
                sync_permissions=True,
            )
            self.available_channel_ids.append(next_channel.id)

            # Rotate active channel to occupied
            current_top_occupied = self.occupied_category.channels[0].position
            await channel.edit(
                category=self.occupied_category,
                position=current_top_occupied,
                sync_permissions=True,
            )

        author: nextcord.Member = message.author
        await author.add_roles(self.get_role("receiving_help"))
        schedule(
            "remove-help-role",
            datetime.timedelta(minutes=15),
            self.remove_help_role,
            author.id,
        )

        beginner = self.get_emoji("beginner")
        intermediate = self.get_emoji("intermediate")
        expert = self.get_emoji("expert")

        await channel.send(
            f"{author.mention} You've claimed this channel! Make sure to clearly ask your question and provide as many "
            f"details as you can *(code, errors, etc.)*, someone will try to help you when they get a chance.\n\nDon't "
            f"forget to give some kudos to show your appreciation by reacting with {beginner}, {intermediate}, or "
            f"{expert}!"
        )

    @tag("schedule", "remove-help-role")
    async def remove_help_role(self, member_id: int):
        member = self.server.get_member(member_id)
        if member:
            await member.remove_roles(self.get_role("receiving_help"))

    async def rotate_occupied_channels(self, message: nextcord.Message):
        async with self.rotation_lock:
            current_top_occupied = self.occupied_category.channels[0].position
            await message.channel.edit(
                category=self.occupied_category, position=current_top_occupied
            )

    def get_next_channel(self) -> nextcord.TextChannel:
        return self.occupied_category.text_channels[-1]

    def is_available_python_help_channel(self, channel: nextcord.TextChannel) -> bool:
        if channel.category_id != self.available_category.id:
            return False

        return channel.name.startswith("🐍python-help-")

    def is_occupied_python_help_channel(self, channel: nextcord.TextChannel) -> bool:
        if channel.category_id != self.occupied_category.id:
            return False

        return channel.name.startswith("🐍python-help-")


def setup(client):
    client.add_cog(HelpRotatorCog(client))
