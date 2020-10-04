from beginner.cog import Cog
from beginner.models.online import OnlineSample
from beginner.scheduler import schedule
from beginner.tags import tag
from datetime import datetime, timedelta
from discord import Embed, Status
from enum import Enum
from peewee import DoesNotExist
from beginner.beginner import BeginnerCog


class OnlineSampleType(Enum):
    MINUTE = "MINUTE"
    MINUTE_10 = "MINUTE_10"
    HOUR = "HOUR"
    DAY = "DAY"
    MONTH = "MONTH"


class StatisticsCog(Cog):
    @Cog.listener()
    async def on_ready(self):
        self.logger.debug("Cog ready")
        self.logger.debug(
            f"{self._get_online_count()} coders are online and {self._get_coders_count()} total coders!!!"
        )
        daily_samples = (
            OnlineSample.select()
            .where(OnlineSample.sample_type == OnlineSampleType.DAY)
            .execute()
        )
        self.logger.debug(f"Found {len(daily_samples)} days of stat samples.")

        await self.online_counter()

    def get_norole(self):
        coders_role = self.get_role("coders")
        count = 0
        for member in self.server.members:
            if not member.bot and coders_role not in member.roles:
                count += 1

        return count

    @Cog.command()
    async def stats(self, ctx):
        month = (
            OnlineSample.select()
            .where(OnlineSample.sample_type == OnlineSampleType.MONTH)
            .order_by(OnlineSample.taken.desc())
            .get()
        )
        today = (
            OnlineSample.select()
            .where(OnlineSample.sample_type == OnlineSampleType.DAY)
            .order_by(OnlineSample.taken.desc())
            .get()
        )
        hour = (
            OnlineSample.select()
            .where(OnlineSample.sample_type == OnlineSampleType.HOUR)
            .order_by(OnlineSample.taken.desc())
            .get()
        )
        highest = self._get_previous_highscore(datetime.now())
        highest_date = (
            f"{highest.taken.day}/{highest.taken.month}/{highest.taken.year}"
            if highest
            else "--/--/----"
        )
        month_name = f"{month.taken:%B}"
        message = (
            f"There are currently {self._get_online_count()} coders online "
            f"of {self._get_coders_count()} coders!!!"
            f"```\n"
            f"                  Most Seen  Least Seen\n"
            f"This Hour         {hour.max_seen:9}  {hour.min_seen:10}\n"
            f"Today             {today.max_seen:9}  {today.min_seen:10}\n"
            f"In {month_name:15}{month.max_seen:9}  {month.min_seen:10}\n"
            f"31 Day High Score {highest.max_seen if highest else '---':9} on {highest_date}"
            f"\n\n{self.get_norole()} have not verified, {len(self.server.members)} total members\n```"
        )
        embed = Embed(description=message, color=0x306998).set_author(
            name=f"Server Statistics{' DEV' if BeginnerCog.is_dev_env() else ''}",
            icon_url=self.server.icon_url,
        )
        await ctx.send(embed=embed)

    @tag("schedule", "statistics", "online-counter")
    async def online_counter(self):
        now = self._clean_time(datetime.now(), "minute")
        scheduled = schedule(
            "online-counter",
            now + timedelta(minutes=1),
            self.online_counter,
            no_duplication=True,
        )
        if scheduled:
            online = self._get_online_count()
            await self._check_for_highscore(now, online)
            self._update_online_count(now, online)
            self._clean_samples(now)

    async def _check_for_highscore(self, now, online):
        sample = self._get_previous_highscore(now)
        self.logger.debug(f"{online} | {sample.max_seen} {sample.taken:%d/%m/%Y}")
        if sample and sample.max_seen < online:
            suffixes = {
                1: "st",
                21: "st",
                31: "st",
                2: "nd",
                22: "nd",
                3: "rd",
                23: "rd",
            }
            suffix = suffixes.get(sample.taken.day, "th")
            message = f"on {sample.taken:%B} {sample.taken.day}{suffix}!"
            if (now - sample.taken).days == 0:
                message = (
                    f" earlier today ({sample.taken:%B} {sample.taken.day}{suffix})!"
                )
            await self.get_channel("staff").send(
                (
                    f"**NEW HIGHSCORE!!!**\nThere are currently {online} coders online!!! "
                    f"That's {online - sample.max_seen} higher than we saw " + message
                )
            )

    def _clean_samples(self, now: datetime):
        OnlineSample.delete().where(
            # Delete all minute samples older than 2 hours
            (
                (OnlineSample.sample_type == OnlineSampleType.MINUTE)
                & (OnlineSample.taken < now - timedelta(hours=2))
            )
            # Delete all 10 minute samples older than a day
            | (
                (OnlineSample.sample_type == OnlineSampleType.MINUTE_10)
                & (OnlineSample.taken < now - timedelta(days=1))
            )
            # Delete all hour samples older than a week
            | (
                (OnlineSample.sample_type == OnlineSampleType.HOUR)
                & (OnlineSample.taken < now - timedelta(days=7))
            )
            # Delete all day samples older than 180 days
            | (
                (OnlineSample.sample_type == OnlineSampleType.DAY)
                & (OnlineSample.taken < now - timedelta(days=180))
            )
        ).execute()

    def _clean_time(self, now: datetime, time_interval: str) -> datetime:
        intervals = ["microsecond", "second", "minute", "hour", "day", "month"]
        interval_minimums = [0, 0, 0, 0, 1, 1]
        return now.replace(
            **{
                interval: minimum
                for minimum, interval in zip(
                    interval_minimums, intervals[: intervals.index(time_interval)]
                )
            }
        )

    def _get_online_count(self) -> int:
        return self._get_coders_count(
            (
                lambda member: not isinstance(member.status, str)
                and member.status != Status.offline,
            )
        )

    def _get_previous_highscore(self, now):
        try:
            return (
                OnlineSample.select()
                .where(
                    (OnlineSample.taken > now - timedelta(days=31))
                    & (OnlineSample.sample_type == OnlineSampleType.DAY)
                )
                .order_by(OnlineSample.max_seen.desc())
                .get()
            )
        except DoesNotExist:
            return None

    def _get_coders_count(self, constraints=tuple()) -> int:
        coders_role = self.get_role("coders")
        count = 0
        for member in self.server.members:
            if coders_role not in member.roles:
                continue

            valid = True
            for constraint in constraints:
                if not constraint(member):
                    valid = False
                    break
            if not valid:
                continue

            count += 1
        return count

    def _update_online_count(self, now: datetime, online: int):
        self._update_online_count_minute(now, online)
        self._update_online_count_minute_10(now, online)
        self._update_online_count_hour(now, online)
        self._update_online_count_day(now, online)
        self._update_online_count_month(now, online)

    def _update_online_count_minute(self, now: datetime, online: int):
        if not OnlineSample.get_or_none(
            OnlineSample.taken == now,
            OnlineSample.sample_type == OnlineSampleType.MINUTE,
        ):
            OnlineSample(
                taken=now, sample_type=OnlineSampleType.MINUTE, max_seen=online
            ).save()

    def _update_online_count_minute_10(self, now: datetime, online: int):
        # Round down to the nearest 10th minute
        taken = now.replace(minute=now.minute - now.minute % 10)
        self._update_online_count_sample(taken, online, OnlineSampleType.MINUTE_10)

    def _update_online_count_hour(self, now: datetime, online: int):
        taken = self._clean_time(now, "hour")
        self._update_online_count_sample(taken, online, OnlineSampleType.HOUR)

    def _update_online_count_day(self, now: datetime, online: int):
        taken = self._clean_time(now, "day")
        self._update_online_count_sample(taken, online, OnlineSampleType.DAY)

    def _update_online_count_month(self, now: datetime, online: int):
        taken = self._clean_time(now, "month")
        self._update_online_count_sample(taken, online, OnlineSampleType.MONTH)

    def _update_online_count_sample(
        self, taken: datetime, online: int, sample_type: OnlineSampleType
    ):
        sample: OnlineSample = OnlineSample.get_or_none(
            OnlineSample.taken == taken, OnlineSample.sample_type == sample_type
        )
        if sample:
            sample.max_seen = max(sample.max_seen, online)
            sample.min_seen = min(sample.min_seen, online)
        else:
            sample = OnlineSample(
                taken=taken, sample_type=sample_type, max_seen=online, min_seen=online
            )
        sample.save()


def setup(client):
    client.add_cog(StatisticsCog(client))
