from collections import Counter
from datetime import datetime, timedelta, timezone
from inspect import isawaitable
from nextcord import Embed, Guild, Member, Message, Role, TextChannel
from typing import Any, Callable, Coroutine, cast, Optional
import ast
import asyncio
import base64
import dippy
import gzip
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
        self._timer: Optional[CallLaterFuture] = CallLaterFuture(
            self._now(), lambda: None
        )
        self._timer.cancel()

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

        if message.author.id == self.client.user.id and self._timer.done():
            return

        if message.author.id == self.disboard.id:
            await self._handle_disboard_message(message)
            return

        await message.delete()

    @dippy.Extension.command("!update bump king")
    async def update_bump_king_admin_command(self, message: Message):
        if not message.author.guild_permissions.administrator:
            return

        bumps = await self._get_bumps(message.guild)
        await self._update_bump_king((0, 0), bumps, message.guild)

    @dippy.Extension.command("!bumpers")
    async def show_bumpers_leaderboard_command(self, message: Message):
        leaderboard = await self._get_leaderboard(message)
        awards = {0: "🥇", 1: "🥈", 2: "🥉"}
        content = []
        for index, (user_id, num_bumps) in enumerate(leaderboard.most_common()):
            award = awards.get(index, "✨")
            user = self.client.get_user(user_id)
            content.append(
                f"{award} {user.mention if user else '*UNKNOWN*'} {num_bumps}"
            )

        await message.channel.send(
            embeds=[
                Embed(
                    color=0xFFCC00,
                    title="🏆 Bumping Leaderboard 🏆",
                    description="\n".join(content),
                )
            ]
        )

    @dippy.Extension.command("!bumps")
    async def list_bumpers_command(self, message: Message):
        bumps = await self._get_bumps(message.guild)
        content = ["**Most Recent**"]
        day_group = 0
        for index, bump in enumerate(bumps, start=1):
            member = message.guild.get_member(bump[0]) or "*UNKNOWN*"
            when = datetime.fromtimestamp(bump[1], tz=timezone.utc)
            days_ago = (self._now() - when) // timedelta(days=1)
            if days_ago != day_group:
                day_group = days_ago
                content.append(f"\n**{days_ago * 24} Hours Ago**")

            content.append(f"{index:>2}. <t:{bump[1]}:t> {member}")

        await message.channel.send(
            embeds=[
                Embed(
                    color=0xFFCC00, title="👊 Bump List", description="\n".join(content)
                )
            ]
        )

    async def _handle_disboard_message(self, message: Message):
        bumper_id = self._get_bumper_id_from_message(message)
        if not bumper_id:
            await message.delete()
            return

        await self._clean_channel(message)
        await self._award_bump_point(message.guild.get_member(bumper_id))
        if not self._timer or self._timer.done():
            self._schedule_reminder(message.created_at + timedelta(hours=2))

    async def _award_bump_point(self, member: Member):
        bumps = await self._get_bumps(member.guild)
        current_king = self._compute_leaderboard(bumps).most_common().pop(0)

        bumps = self._cleanup_bumps(bumps)
        bumps.insert(0, (member.id, int(self._now().timestamp())))
        await self._set_bumps(member.guild, bumps)

        await self._update_bump_king(current_king, bumps, member.guild)

    async def _update_bump_king(
        self, current_king: tuple[int, int], bumps: list[tuple[int, int]], guild: Guild
    ):
        leaderboard = self._compute_leaderboard(bumps)
        updated_king = leaderboard.most_common().pop(0)
        if current_king[0] == updated_king[0]:
            return

        member = guild.get_member(updated_king[0])
        if not member:
            return

        next_highest = leaderboard.most_common().pop(1)
        if next_highest[1] == updated_king[1] and not self._bumped_more_recently(
            updated_king[0], next_highest[0], bumps
        ):
            return

        role = guild.get_role(715584554861330465)
        await asyncio.gather(
            *(m.remove_role(role) for m in role.members if m.id != member.id),
            member.add_roles(role),
            guild.get_channel(876944510200991756).send(
                embeds=[
                    Embed(
                        color=0xFFCC00,
                        title="👑 All Hail The Bump King 👊",
                        description=f"All hail our new 🍕 Bump King 🍕 {member.mention}!!!",
                    )
                ]
            ),
        )

    def _bumped_more_recently(self, this_user_id, than_user_id, bumps):
        for user_id, _ in bumps:
            if user_id == this_user_id:
                break
            elif user_id == than_user_id:
                return False

        return True

    async def _get_bumps(self, guild: Guild) -> list[tuple[int, int]]:
        raw_bumps: str = await guild.get_label("bumps", default="")
        self.log.info(f"Raw bumps: {raw_bumps!r}")
        if not raw_bumps:
            return []

        bumps = ast.literal_eval(
            gzip.decompress(base64.b64decode(raw_bumps.encode())).decode()
        )
        self.log.info(f"Bumps: {bumps!r}")
        return bumps

    async def _set_bumps(
        self, guild: Guild, bumps: list[tuple[int, int]]
    ) -> list[tuple[int, int]]:
        await guild.set_label(
            "bumps", base64.b64encode(gzip.compress(str(bumps).encode())).decode()
        )

    def _cleanup_bumps(self, bumps: list[tuple[int, int]]) -> list[tuple[int, int]]:
        oldest = (self._now() - timedelta(days=7)).timestamp()
        return [bump for bump in bumps if bump[1] >= oldest]

    async def _get_leaderboard(self, message: Message):
        bumps = await self._get_bumps(message.guild)
        return self._compute_leaderboard(bumps)

    def _compute_leaderboard(self, bumps):
        return Counter(user_id for user_id, _ in bumps)

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
        await self._clean_channel()
        await self.bump_channel.send(
            f"{self.bumper_role.mention} It's been 2hrs since the last bump!\n*Use the `/bump` command now!*"
        )

    async def _clean_channel(self, ignore: Optional[Message] = None):
        def check(message: Message):
            if ignore and message.id == ignore.id:
                return False

            return self._now() - message.created_at < timedelta(hours=3)

        await self.bump_channel.purge(check=check)
