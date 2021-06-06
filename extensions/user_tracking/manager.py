from __future__ import annotations
from bevy import Injectable
from dataclasses import dataclass, field
from dippy.labels.storage import StorageInterface
from discord import Member
from datetime import datetime
from typing import Optional, Union


__all__ = ["UserTracker"]


@dataclass
class UsernameHistory:
    old_username: str
    new_username: str
    date: datetime = field(default_factory=datetime.utcnow)

    def serialize(self) -> tuple[str, str]:
        return self.old_username, self.new_username, self.date.isoformat()

    @classmethod
    def create(
        cls,
        old_username: str,
        new_username: str,
        date: Optional[Union[datetime, str]] = None,
    ) -> UsernameHistory:
        args = [old_username, new_username]
        if isinstance(date, str):
            date = datetime.fromisoformat(date)
        if isinstance(date, datetime):
            args.append(date)
        return cls(*args)


class UserTracker(Injectable):
    labels: StorageInterface

    async def get_username_history(self, member: Member) -> list[UsernameHistory]:
        history = await self._get_history(member)
        return [UsernameHistory.create(*entry) for entry in history]

    async def add_username_to_history(self, member: Member, name: str):
        history = await self._get_history(member)
        history.append(UsernameHistory.create(name, member.display_name).serialize())
        await self._save_history(member, history[-10:])

    async def _get_history(self, member: Member) -> list[tuple[str, str, str]]:
        return await self.labels.get(
            f"member[{member.guild.id}]", member.id, "username_history", []
        )

    async def _save_history(self, member: Member, history: list[tuple[str, str, str]]):
        await self.labels.set(
            f"member[{member.guild.id}]", member.id, "username_history", history
        )
