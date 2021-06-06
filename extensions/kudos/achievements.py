from bevy import Injectable
from collections import UserDict
from dataclasses import dataclass, field
from dippy import Client
from discord import Member, utils, errors
from typing import Callable, Coroutine


@dataclass
class Achievement:
    name: str
    description: str
    unlock_description: str
    emoji: str
    kudos: int
    awarded_handlers: set[Callable[[Member], Coroutine]] = field(default_factory=set)

    def on_awarded(self, callback: Callable[[Member], Coroutine]):
        self.awarded_handlers.add(callback)

    def __hash__(self):
        return hash(self.name)


class Achievements(UserDict, Injectable):
    client: Client

    def __init__(self):
        super().__init__(
            {
                "MUSIC_DJ": Achievement(
                    "Music DJ",
                    (
                        "Music DJs get the 🎸Music DJ🎸 role while in voice chat allowing them full control of the "
                        "Rythm music bot."
                    ),
                    (
                        "You're a Music DJ! When in voice chat you'll have the DJ role giving you full control of the "
                        "Rythm music bot!"
                    ),
                    "🎸",
                    250,
                ),
                "CODER": Achievement(
                    "Coder",
                    (
                        "Coders are the members who are most active in our community, asking questions, helping "
                        "others, participating in the fun, doing challenges, etc."
                    ),
                    "You're a Coder! Thanks for being 😎 AWESOME 😎!!!",
                    "😎",
                    112,
                ),
            }
        )

        self.on_award("CODER", self.give_coders_role)

    async def awarded_achievement(self, member: Member, achievement: Achievement):
        if achievement.awarded_handlers:
            for handler in achievement.awarded_handlers:
                self.client.loop.create_task(handler(member))

    def on_award(self, achievement_key: str, callback: Callable[[Member], Coroutine]):
        self[achievement_key].on_awarded(callback)

    async def give_coders_role(self, member: Member):
        role = utils.get(member.guild.roles, name="coders")
        try:
            await member.add_roles(role)
            await member.remove_roles()
            await self.client.get_channel(851228622832533534).send(
                f"{member.mention} you're awesome! Thank you for contributing and being such an amazing part of this "
                f"community! Now that you've unlocked the 😎Coders😎 achievement you have access to this channel!"
            )
        except errors.Forbidden:
            pass
