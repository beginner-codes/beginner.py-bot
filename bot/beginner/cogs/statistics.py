from beginner.cog import Cog
from beginner.models.online import OnlineSample
from beginner.scheduler import schedule
from beginner.tags import tag
from datetime import datetime, timedelta
from discord import Embed, Status
from enum import Enum


class OnlineSampleType(Enum):
    MINUTE = "MINUTE"
    MINUTE_10 = "MINUTE_10"
    HOUR = "HOUR"
    DAY = "DAY"
    MONTH = "MONTH"


class StatisticsCog(Cog):
    @Cog.listener()
    async def on_ready(self):
        print(self._get_online_count(), "coders are online")
        self.online_counter()
        samples = OnlineSample.select()

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
        last_10 = (
            OnlineSample.select()
            .where(OnlineSample.sample_type == OnlineSampleType.MINUTE_10)
            .order_by(OnlineSample.taken.desc())
            .get()
        )
        embed = Embed(
            description=f"There are currently {self._get_online_count()} coders online!!!",
            color=0x306998,
        ).set_author(name=f"Server Statistics", icon_url=self.server.icon_url)
        embed.add_field(
            name="Period", value="10 Minutes\nHour\nDay\nMonth", inline=True
        )
        embed.add_field(
            name="Most Seen",
            value=f"{last_10.max_seen}\n{hour.max_seen}\n{today.max_seen}\n{month.max_seen}",
            inline=True,
        )
        embed.add_field(
            name="Least Seen",
            value=f"{last_10.min_seen}\n{hour.min_seen}\n{today.min_seen}\n{month.min_seen}",
            inline=True,
        )
        await ctx.send(embed=embed)

    @tag("schedule", "statistics", "online-counter")
    def online_counter(self):
        now = self._clean_time(datetime.now(), "minute")
        online = self._get_online_count()
        scheduled = schedule(
            "online-counter",
            now + timedelta(minutes=1),
            self.online_counter,
            no_duplication=True,
        )
        if scheduled:
            self._update_online_count(now, online)
            self._clean_samples(now)

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
        coders_role = self.get_role("coders")
        count = 0
        for member in self.server.members:
            if isinstance(member.status, str) or member.status == Status.offline:
                continue
            if coders_role not in member.roles:
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
