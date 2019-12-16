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
        print(f"{'TAKEN':20} | {'MAX':4} | {'MIN':4} | TYPE")
        for sample in samples:
            print(
                f"{sample.taken.isoformat():20} | {sample.max_seen:4} | {'-' if sample.min_seen is None else sample.min_seen:4} | {sample.sample_type}"
            )

    @Cog.command()
    async def stats(self, ctx):
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
        embed.add_field(name="Period", value="10 Minutes\nHour\nDay", inline=True)
        embed.add_field(
            name="Most Seen",
            value=f"{last_10.max_seen}\n{hour.max_seen}\n{today.max_seen}",
            inline=True,
        )
        embed.add_field(
            name="Least Seen",
            value=f"{last_10.min_seen}\n{hour.min_seen}\n{today.min_seen}",
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
        minute_10_sample: OnlineSample = OnlineSample.get_or_none(
            OnlineSample.taken == taken,
            OnlineSample.sample_type == OnlineSampleType.MINUTE_10,
        )
        if minute_10_sample:
            minute_10_sample.max_seen = max(minute_10_sample.max_seen, online)
            minute_10_sample.min_seen = min(minute_10_sample.min_seen, online)
        else:
            minute_10_sample = OnlineSample(
                taken=taken,
                sample_type=OnlineSampleType.MINUTE_10,
                max_seen=online,
                min_seen=online,
            )
        minute_10_sample.save()

    def _update_online_count_hour(self, now: datetime, online: int):
        taken = self._clean_time(now, "hour")
        hour_sample: OnlineSample = OnlineSample.get_or_none(
            OnlineSample.taken == taken,
            OnlineSample.sample_type == OnlineSampleType.HOUR,
        )
        if hour_sample:
            hour_sample.max_seen = max(hour_sample.max_seen, online)
            hour_sample.min_seen = min(hour_sample.min_seen, online)
        else:
            hour_sample = OnlineSample(
                taken=taken,
                sample_type=OnlineSampleType.HOUR,
                max_seen=online,
                min_seen=online,
            )
        hour_sample.save()

    def _update_online_count_day(self, now: datetime, online: int):
        taken = self._clean_time(now, "day")
        day_sample: OnlineSample = OnlineSample.get_or_none(
            OnlineSample.taken == taken,
            OnlineSample.sample_type == OnlineSampleType.DAY,
        )
        if day_sample:
            day_sample.max_seen = max(day_sample.max_seen, online)
            day_sample.min_seen = min(day_sample.min_seen, online)
        else:
            day_sample = OnlineSample(
                taken=taken,
                sample_type=OnlineSampleType.DAY,
                max_seen=online,
                min_seen=online,
            )
        day_sample.save()

    def _update_online_count_month(self, now: datetime, online: int):
        taken = self._clean_time(now, "month")
        month_sample: OnlineSample = OnlineSample.get_or_none(
            OnlineSample.taken == taken,
            OnlineSample.sample_type == OnlineSampleType.MONTH,
        )
        if month_sample:
            month_sample.max_seen = max(month_sample.max_seen, online)
            month_sample.min_seen = min(month_sample.min_seen, online)
        else:
            month_sample = OnlineSample(
                taken=taken,
                sample_type=OnlineSampleType.MONTH,
                max_seen=online,
                min_seen=online,
            )
        month_sample.save()


def setup(client):
    client.add_cog(StatisticsCog(client))
