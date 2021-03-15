from __future__ import annotations
from beginner.cog import Cog
from dataclasses import dataclass
from discord import Message
from discord.ext.commands import Context
from typing import Dict, Tuple
import random


@dataclass
class MontyHallGame:
    player_choice: int
    options: Tuple[bool, ...]
    channel_id: int
    state: str = "choosing"

    def get_remaining_losing_option(self) -> int:
        options = [
            index
            for index, option in enumerate(self.options)
            if index != self.player_choice and not option
        ]
        return random.choice(options)

    def is_winner(self) -> bool:
        return self.options[self.player_choice]


class LuckPromptCog(Cog):
    def __init__(self, client):
        super().__init__(client)
        self.games: Dict[int, MontyHallGame] = {}

    @Cog.command()
    async def lucky(self, ctx: Context):
        winning_option = random.randint(0, 2)
        options = tuple(index == winning_option for index in range(3))
        self.games[ctx.author.id] = MontyHallGame(-1, options, ctx.channel.id)

        await ctx.send(
            f"{ctx.author.mention} let's play a game to see if you're lucky. There are three options:\n"
            f"**A B C**\n"
            f"Only one of these is lucky, which do you think it is?"
        )

    @Cog.listener()
    async def on_message(self, message: Message):
        if message.author.id not in self.games:
            return

        game = self.games[message.author.id]
        if message.channel.id != game.channel_id:
            return

        content = message.content.strip().casefold()

        if game.state == "choosing":
            if content not in "abc":
                return

            game.player_choice = "abc".index(content)
            game.state = "switching"

            reveal = "ABC"[game.get_remaining_losing_option()]
            last = (set("ABC") - set(reveal + "ABC"[game.player_choice])).pop()
            await message.channel.send(
                f"{message.author.mention} you chose {content.upper()}\n"
                f"Since we like you we're gonna give you the option to switch your choice. Because we're so cool, we'll"
                f" even tell you that option {reveal} is not lucky.\n"
                f"Would you like to switch to {last}? *(yes or no)*"
            )

        elif game.state == "switching":
            if content not in {"yes", "no"}:
                return

            switch = content == "yes"
            switch_text = "to switch" if switch else "not to switch"
            won = (
                "**✨ YOU'RE LUCKY ✨**"
                if game.is_winner() != switch
                else "You're not lucky 😕"
            )

            await message.channel.send(
                f"{message.author.mention} you chose {switch_text}\n{won}"
            )

            del self.games[message.author.id]


def setup(client):
    client.add_cog(LuckPromptCog(client))
