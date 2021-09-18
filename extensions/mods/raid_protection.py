from asyncio import get_running_loop
from datetime import datetime, timedelta, timezone
from dippy.sqlalchemy_connector import SQLAlchemyConnector
from extensions.mods.mod_manager import ModManager
from enum import Enum
from nextcord import (
    Guild,
    Member,
    Message,
    User,
)
from sqlalchemy import Column, DateTime, Integer, BigInteger, String
import dippy
import statistics


class ActivityType(str, Enum):
    MEMBER_JOIN = "MEMBER_JOIN"
    MEMBER_LEAVE = "MEMBER_JOIN"
    MEMBER_BANNED = "MEMBER_BANNED"
    MEMBER_UNBANNED = "MEMBER_UNBANNED"

    def __str__(self):
        return self.value


class ActivityEntry(SQLAlchemyConnector.BaseModel):
    __tablename__ = "activity_entries"

    id = Column(Integer, primary_key=True)
    activity_type = Column(String(32), nullable=False)
    date = Column(DateTime, nullable=False)
    target_id = Column(BigInteger, nullable=False)
    guild_id = Column(BigInteger, nullable=False)


class RaidProtection(dippy.Extension):
    client: dippy.Client
    db: SQLAlchemyConnector
    mod_manager: ModManager

    def __init__(self):
        super().__init__()
        self.db.create_tables()

    async def add_activity_entry(
        self, activity_type: ActivityType, target_id: int, guild_id: int
    ):
        def _add_to_db():
            with self.db.session() as session:
                label = ActivityEntry(
                    activity_type=str(activity_type),
                    target_id=target_id,
                    guild_id=guild_id,
                    date=datetime.utcnow(),
                )
                session.add(label)
                session.commit()

        await get_running_loop().run_in_executor(None, _add_to_db)

    async def get_activity_entries(
        self, activity_type: ActivityType, guild_id: int, date: datetime
    ) -> list[ActivityEntry]:
        def _query_db() -> list[ActivityEntry]:
            with self.db.session() as session:
                query = (
                    session.query(ActivityEntry)
                    .filter(ActivityEntry.activity_type == activity_type)
                    .filter(ActivityEntry.date > date)
                    .filter(ActivityEntry.guild_id == guild_id)
                    .order_by(ActivityEntry.date.desc())
                )
                results = list(query.all())
                session.expunge_all()
                return results

        return await get_running_loop().run_in_executor(None, _query_db)

    @dippy.extensions.Extension.command("!join info")
    async def show_join_info(self, message: Message):
        if not message.author.guild_permissions.manage_messages:
            return

        week = timedelta(days=7)

        bans = await self._get_bans(message.guild, week)
        joins = await self._get_joins_by_hour(message.guild, week, bans)
        last_5_minutes_joins = await self.get_activity_entries(
            ActivityType.MEMBER_JOIN,
            message.guild.id,
            self._now() - timedelta(minutes=5),
        )
        most_recent = joins.pop(0)
        mu = statistics.mean(joins.values()) if joins else 0
        degree_of_variation = self._get_degree_of_variation(joins)
        alert_started = await self.mod_manager.alert_active(message.guild)
        alert = "No"
        if alert_started == 0:
            alert = "Just Now"
        elif alert_started > 0:
            alert = f"{alert_started} minute{'s' * (alert_started != 1)}"
        await message.channel.send(
            f"Join Periods: {len(joins)}\n"
            f"Mean: {mu}\n"
            f"Most Recent: {most_recent}\n"
            f"Degree of Variation: {degree_of_variation}\n"
            f"Last 5 Minutes: {len(last_5_minutes_joins)}\n"
            f"Alert Active: {alert}"
        )

    @dippy.extensions.Extension.listener("member_join")
    async def add_member_join_to_activity_history(self, member: Member):
        await self.add_activity_entry(
            ActivityType.MEMBER_JOIN, member.id, member.guild.id
        )
        await self._scan_for_raid(member.guild)

    @dippy.extensions.Extension.listener("member_remove")
    async def add_member_leave_to_activity_history(self, member: Member):
        await self.add_activity_entry(
            ActivityType.MEMBER_LEAVE, member.id, member.guild.id
        )

    @dippy.extensions.Extension.listener("member_ban")
    async def add_member_ban_to_activity_history(self, guild: Guild, user: User):
        await self.add_activity_entry(ActivityType.MEMBER_BANNED, user.id, guild.id)

    @dippy.extensions.Extension.listener("member_unban")
    async def add_member_unban_to_activity_history(self, guild: Guild, user: User):
        await self.add_activity_entry(ActivityType.MEMBER_UNBANNED, user.id, guild.id)

    async def _get_bans(self, guild: Guild, duration: timedelta) -> list[int]:
        since = self._now() - duration
        unbans = await self.get_activity_entries(
            ActivityType.MEMBER_UNBANNED, guild.id, since
        )
        unbans = [entry.target_id for entry in unbans]
        bans = await self.get_activity_entries(
            ActivityType.MEMBER_BANNED, guild.id, since
        )
        return [entry.target_id for entry in bans if entry.target_id not in unbans]

    def _get_degree_of_variation(self, joins: dict[int, int]) -> float:
        most_recent = joins.pop(0, 0)
        mu = statistics.mean(joins.values()) if joins else 0
        if most_recent <= mu:
            return 0

        standard_deviation = statistics.pstdev(joins[:-1], mu=mu)
        recent_deviation = statistics.pstdev(joins[-1:], mu=mu)
        if recent_deviation < standard_deviation:
            return 0

        return (recent_deviation - standard_deviation) / standard_deviation

    async def _get_joins_by_hour(
        self, guild: Guild, duration: timedelta, bans: list[int]
    ) -> dict[int, int]:
        now = self._now()
        period = timedelta(hours=1)
        joins_by_hour = {0: 0}

        for entry in await self.get_activity_entries(
            ActivityType.MEMBER_JOIN, guild.id, now - duration
        ):
            if entry.target_id not in bans:
                joins_by_hour[
                    (now - entry.date.astimezone(timezone.utc)) // period
                ] += 1

        return joins_by_hour

    def _now(self) -> datetime:
        return datetime.now().astimezone(timezone.utc)

    async def _lockdown(self, guild: Guild):
        if await self.mod_manager.locked_down(guild):
            return
        await self.mod_manager.lockdown(guild, guild.get_channel(720663441966366850))

    async def _alert(self, guild: Guild):
        if await self.mod_manager.locked_down(guild):
            return

        await self.mod_manager.start_alert(guild)
        await guild.get_channel(720663441966366850).send(
            "There's been an increase in joins. Watch out for a raid. @mods can use `!lockdown` to prevent new members "
            "from interacting with the server."
        )

    async def _do_spike_raid_check(self, guild: Guild) -> bool:
        joins = await self.get_activity_entries(
            ActivityType.MEMBER_JOIN, guild.id, self._now() - timedelta(minutes=5)
        )
        if len(joins) > 10:
            await self._lockdown(guild)

        elif len(joins) > 5:
            await self._alert(guild)

        return len(joins) > 5

    async def _do_out_of_bounds_raid_check(self, guild: Guild) -> bool:
        week = timedelta(days=7)

        bans = await self._get_bans(guild, week)
        joins = await self._get_joins_by_hour(guild, week, bans)

        if len(joins) < timedelta(days=5) // timedelta(hours=1):
            return False

        degree_of_variation = self._get_degree_of_variation(joins)
        if degree_of_variation > 0.05:
            await guild.get_channel(644309581476003860).send(
                f"ALERT Degree of variation is {degree_of_variation}"
            )

        if degree_of_variation > 0.1:
            await guild.get_channel(644309581476003860).send(
                f"LOCKDOWN Degree of variation is {degree_of_variation}"
            )

    async def _scan_for_raid(self, guild: Guild):
        if await self._do_spike_raid_check(guild):
            return

        if await self._do_out_of_bounds_raid_check(guild):
            return
