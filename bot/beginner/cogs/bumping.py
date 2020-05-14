from beginner.cog import Cog
from beginner.scheduler import schedule, task_scheduled
from beginner.tags import tag
from datetime import datetime, timedelta
import asyncio
import discord
import re
import os


class Bumping(Cog):
    @Cog.listener()
    async def on_ready(self):
        self.channel = self.get_channel(os.environ.get("BUMP_CHANNEL", "bumping"))
        self.disboard = self.server.get_member(302050872383242240)
        self.explanation_message = await self.get_explanation_message()
        self.role = self.get_role("bumpers")
        self.logger.debug("Cog ready")

    @Cog.command()
    async def d(self, ctx, option):
        if option != "bump":
            return

        self.logger.debug(f"BUMP RECEIVED FROM {ctx.author.display_name}")

        if not hasattr(self, "channel") or ctx.message.channel != self.channel:
            return

        def is_confirmation(message):
            if not self.is_bump_confirmation(message):
                return False

            mention_id = int(re.findall(r"\d+", message.embeds[0].description)[0])
            if ctx.message.author.id != mention_id:
                return False

            return True

        try:
            confirmation_message = await self.client.wait_for(
                "message", check=is_confirmation, timeout=10
            )
        except asyncio.TimeoutError:
            if task_scheduled("bump-reminder"):
                await ctx.message.delete()
            else:
                await self.handle_disboard_down()
        else:
            await self.handle_new_bump(ctx.message, confirmation_message)

    async def handle_new_bump(self, bump_message, confirmation_message):
        if task_scheduled("bump-reminder"):
            await self.channel.delete_messages([bump_message, confirmation_message])
        else:
            await self.delete_all_except(bump_message, confirmation_message)
            schedule(
                "bump-reminder",
                timedelta(minutes=self.get_next_bump_timer(confirmation_message)),
                self.bump_reminder,
                no_duplication=True,
            )

    async def handle_disboard_down(self):
        self.logger.debug(f"Disboard may be down: {self.disboard.status}")
        await self.delete_all_except()
        await self.channel.send(
            embed=discord.Embed(
                description=(
                    f"{self.disboard.mention} appears to be offline. "
                    f"I'll monitor its status and let you know when it is back online."
                ),
                color=0xCC2222,
            )
        )
        await self.bump_recovery()

    async def delete_all_except(self, *messages):
        message_ids = {m.id for m in messages}

        def should_delete(message):
            if (datetime.utcnow() - message.created_at).days > 7:
                return False

            return message.id not in message_ids

        await self.channel.purge(
            limit=1000,
            check=should_delete,
            after=self.explanation_message,
            oldest_first=False,
        )

    @Cog.listener()
    async def on_message(self, message):
        if not hasattr(self, "channel") or message.channel != self.channel:
            return

        if message.content == "!d bump":
            return

        if self.is_bump_confirmation(message):
            return

        if message.author.id == self.server.me.id:
            if "It's been 2hrs since the last bump!" in message.content:
                return

            if "tagged by bump reminders" in message.content:
                return

            if (
                not hasattr(self, "explanation_message")
                or self.explanation_message == None
            ):
                return

        if (
            len(message.embeds)
            and "appears to be offline" in message.embeds[0].description
        ):
            return

        await message.delete()

    def is_bump_confirmation(self, message):
        return self.is_bump_success_confirmation(
            message
        ) or self.is_bump_fail_confirmation(message)

    def is_bump_success_confirmation(self, message):
        if len(message.embeds) == 0:
            return False

        if message.author.id != self.disboard.id:
            return False

        return "Bump done" in message.embeds[0].description

    def is_bump_fail_confirmation(self, message):
        if len(message.embeds) == 0:
            return False

        if message.author.id != self.disboard.id:
            return False

        return "Please wait" in message.embeds[0].description

    def get_next_bump_timer(self, message):
        result = re.findall(r"\d+", message.embeds[0].description)
        timer = 120
        if len(result) > 1:
            timer = int(result[-1])
        return timer

    @tag("schedule", "disboard-bump-reminder")
    async def bump_reminder(self):
        self.logger.debug(f"SENDING BUMP REMINDER: {self.role.name}")
        if self.disboard.status == discord.Status.online:
            await self.delete_all_except()
            await self.channel.send(
                f"{self.role.mention} It's been 2hrs since the last bump!\n"
                f"*Use the command `!d bump` now!*"
            )
        else:
            await self.handle_disboard_down()

    @tag("schedule", "disboard-bump-recovery")
    async def bump_recovery(self):
        self.logger.debug(f"ATTEMPTING BUMP RECOVERY")
        if self.disboard.status == discord.Status.online:
            await self.bump_reminder()
        else:
            schedule(
                "bump-recovery",
                timedelta(minutes=1),
                self.bump_recovery,
                no_duplication=True,
            )

    @Cog.listener()
    async def on_raw_reaction_add(self, reaction):
        if reaction.emoji.name != "🔔":
            return

        if reaction.message_id != self.explanation_message.id:
            return

        member = self.server.get_member(reaction.user_id)
        if member.bot:
            return

        if self.role not in member.roles:
            await self.add_bumper_role(member)

    @Cog.listener()
    async def on_raw_reaction_remove(self, reaction):
        if reaction.emoji.name != "🔔":
            return

        if reaction.message_id != self.explanation_message.id:
            return

        member = self.server.get_member(reaction.user_id)
        if member.bot:
            return

        if self.role in member.roles:
            await self.remove_bumper_role(member)

    async def add_bumper_role(self, member):
        await member.add_roles(self.role)
        await self.channel.send(
            f"{member.mention} you will be tagged by bump reminders", delete_after=10
        )

    async def clean_up_messages(self):
        messages = self.channel.history(
            after=self.explanation_message, oldest_first=False
        )
        deleting = []
        bump = None
        confirmation = None
        success = False
        async for message in messages:
            if (datetime.utcnow() - message.created_at).days > 7:
                break

            elif not success and self.is_bump_success_confirmation(message):
                if confirmation:
                    deleting.append(confirmation)

                    if bump:
                        deleting.append(bump)

                success = True
                confirmation = message
                bump = None

            elif not confirmation and self.is_bump_fail_confirmation(message):
                confirmation = message

            elif message.content == "!d bump" and not bump:
                bump = message

            elif message.author.id == self.server.me.id and (
                not message.content.endswith("Use the command `!d bump` now!*")
                or not confirmation
            ):
                pass

            else:
                deleting.append(message)

        await self.channel.delete_messages(deleting)

    async def create_explanation_message(self):
        message = await self.channel.send(
            embed=discord.Embed(
                description=(
                    f"To help us stay at the top of Disboard join the *Bump Squad* by reacting with the 🔔, "
                    f"react again to leave the squad"
                ),
                color=0x306998,
            ).set_author(name="Beginner.py Bump Squad", icon_url=self.server.icon_url)
        )
        await message.add_reaction("🔔")
        return message

    async def get_explanation_message(self):
        messages = await self.channel.history(oldest_first=True, limit=1).flatten()
        if len(messages) == 0:
            return await self.create_explanation_message()
        return messages[0]

    async def remove_bumper_role(self, member):
        await member.remove_roles(self.role)
        await self.channel.send(
            f"{member.mention} you will no longer be tagged by bump reminders",
            delete_after=10,
        )


def setup(client):
    client.add_cog(Bumping(client))
