from datetime import datetime, timedelta, timezone
from inspect import isawaitable
from nextcord import Member, Message, Role, TextChannel
from typing import Any, Callable, Coroutine, cast, Optional
import asyncio
import dippy
import re


class CallLaterFuture(asyncio.Future):
    def __init__(
        self,
        when: datetime,
        callback: Callable[[], Optional[Coroutine[Any, Any, None]]],
        *,
        loop=None,
    ):
        super().__init__(loop=loop)
        self.callback = callback
        self.when = when
        self.handler = self._create_task()

    def cancel(self, msg: Optional[str] = ...) -> bool:
        self.handler.cancel()
        return super().cancel(msg)

    def _create_task(self):
        return self.get_loop().call_later(
            (self.when - datetime.now(tz=timezone.utc)).total_seconds(), self._run
        )

    def _run(self):
        self.set_result(True)
        result = self.callback()
        if isawaitable(result):
            self.get_loop().create_task(result)


class DisboardBumpReminderExtension(dippy.Extension):
    client: dippy.Client
    log: dippy.logging.Logging

    def __init__(self):
        super().__init__()
        self._timer: Optional[CallLaterFuture] = None

    @property
    def bump_channel(self) -> TextChannel:
        return cast(TextChannel, self.client.get_channel(702178352395583498))

    @property
    def bumper_role(self) -> Role:
        return self.bump_channel.guild.get_role(702177774315634788)

    @property
    def disboard(self) -> Member:
        return self.bump_channel.guild.get_member(302050872383242240)

    @dippy.Extension.listener("ready")
    async def on_ready(self):
        self.log.info("Disboard bump reminder setting up")
        await self._setup_reminders()

    @dippy.Extension.listener("message")
    async def on_message(self, message: Message):
        if message.channel != self.bump_channel:
            return

        if (
            message.author is not self.disboard
            or message.author.id != self.client.user.id
        ):
            await message.delete()
            return

        await self._handle_disboard_message(message)

    async def _handle_disboard_message(self, message: Message):
        bumper_id = self._get_bumper_id_from_message(message)
        if not bumper_id:
            return

        if not self._timer or self._timer.done():
            self._schedule_reminder(message.created_at + timedelta(hours=2))

    async def _setup_reminders(self):
        last_success = await self._find_last_bump_success()
        if self._now() - last_success > timedelta(hours=2):
            await self._send_bump_reminder()
        else:
            self._schedule_reminder(last_success + timedelta(hours=2))

    async def _find_last_bump_success(self) -> datetime:
        async for message in self.bump_channel.history():
            if message.author == self.disboard:
                bumper_id = self._get_bumper_id_from_message(message)
                if bumper_id:
                    return message.created_at

        return self._now()

    def _get_bumper_id_from_message(self, message: Message) -> Optional[int]:
        if not message.embeds:
            return

        match = re.search(r"^<@(\d+)> Bump done!", message.embeds[0].description)
        if not match:
            return

        return int(match.groups()[0])

    def _now(self) -> datetime:
        return datetime.now(tz=timezone.utc)

    def _schedule_reminder(self, when: datetime):
        if self._timer and not self._timer.done():
            self._timer.cancel()

        self.log.info(f"Scheduling next Disboard reminder for {when.isoformat()}")
        self._timer = CallLaterFuture(when, self._send_bump_reminder)

    async def _send_bump_reminder(self):
        await self.bump_channel.purge(limit=1)
        await self.bump_channel.send(
            f"{self.bumper_role.mention} It's been 2hrs since the last bump!\n*Use the `/bump` command now!*"
        )
