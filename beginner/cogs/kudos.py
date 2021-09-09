import beginner.kudos as kudos
import nextcord
import os
from beginner.cog import Cog, commands
from beginner.colors import *
from datetime import datetime, timedelta
from typing import Dict
from io import BytesIO


class Kudos(Cog):
    def __init__(self, client):
        super().__init__(client)
        self.dev_author = int(os.environ.get("DEV_AUTHOR_ID", 0))
        self._reactions = {}

    @property
    def point_values(self) -> Dict[str, int]:
        return {
            "good": self.settings.get("kudos.score.good", 2),
            "great": self.settings.get("kudos.score.great", 4),
            "excellent": self.settings.get("kudos.score.excellent", 8),
        }

    @property
    def pool_size(self) -> int:
        return self.settings.get("kudos.pool.size", self.point_values["excellent"])

    @property
    def pool_regeneration(self):
        return self.settings.get("kudos.pool.regeneration", 12)

    @property
    def reactions(self):
        if not self._reactions:
            self._reactions = {
                "good": self.get_emoji("beginner"),
                "great": self.get_emoji("intermediate"),
                "excellent": self.get_emoji("expert"),
            }
            self._reactions.update(
                {emoji.id: name for name, emoji in self.reactions.items()}
            )
        return self._reactions

    @Cog.command()
    async def exportkudos(self, ctx: commands.Context):
        scores = kudos.get_highest_kudos(100000)
        file = BytesIO()
        file.writelines(
            f"{member_id},{points}\n".encode() for member_id, points in scores
        )
        file.seek(0)
        await ctx.send(
            f"User kudos totals as of {datetime.utcnow().date().isoformat()}",
            file=nextcord.File(
                file,
                filename=f"member-kudos-{datetime.utcnow().date().isoformat().replace('-', '')}.csv",
            ),
        )

    @Cog.command(aliases=["k"])
    async def kudos(self, ctx: commands.Context, option: str = ""):
        if not self.settings.get("KUDOS_ENABLED", True):
            return

        if self.dev_author and ctx.author.id != self.dev_author:
            return

        if ctx.author.bot:
            return

        if option.casefold() in {"help", "h"}:
            await ctx.send(
                embed=(
                    nextcord.Embed(
                        color=YELLOW,
                        description=(
                            "Users can give kudos to anyone that they feel deserves recognition. It might be for help "
                            "they gave or a cool project they shared or a useful resource they linked."
                        ),
                    )
                    .add_field(
                        name="Levels of Kudos",
                        inline=False,
                        value=(
                            f"{self.reactions['good']} *Good* gives {self.point_values['good']} points\n"
                            f"{self.reactions['great']} *Great* gives {self.point_values['great']} points\n"
                            f"{self.reactions['excellent']} *Excellent* gives {self.point_values['excellent']} points"
                        ),
                    )
                    .add_field(
                        name="Giving Kudos",
                        inline=False,
                        value=(
                            f"To give kudos just react to any message with one of the above emoji to award the "
                            f"corresponding amount of kudos. You only have {self.pool_size} kudos to give, and it will "
                            f"regenerate 1 point every {self.pool_regeneration} minute"
                            f"{'s' if self.pool_regeneration else ''}."
                        ),
                    )
                    .add_field(
                        name="Leaderboard",
                        inline=False,
                        value="You can see a kudos leader board by using `!kudos leaderboard`.",
                    )
                    .set_author(name="Kudos - Help", icon_url=self.server.icon.url)
                    .set_thumbnail(
                        url="https://cdn.discordapp.com/emojis/669941420454576131.png?v=1"
                    )
                )
            )
            return

        author_kudos = kudos.get_user_kudos(ctx.author.id)
        message = [
            f"{ctx.author.mention} you have {author_kudos if author_kudos > 0 else 'no'} kudos"
        ]
        if author_kudos == 0:
            message.append(
                "\nKeep helping and contributing and you're bound to get some kudos!"
            )

        embed = (
            nextcord.Embed(color=BLUE, description="\n".join(message))
            .set_author(name="Kudos", icon_url=self.server.icon.url)
            .set_thumbnail(
                url="https://cdn.discordapp.com/emojis/669941420454576131.png?v=1"
            )
        )

        footer = "'!kudos help' or '!kudos leaderboard'"

        if option.casefold() in {
            "leaderboard",
            "lb",
            "l",
            "leaders",
            "highscores",
            "hs",
        }:
            leader_board = []
            for index, (member_id, member_kudos) in enumerate(
                kudos.get_highest_kudos(5)
            ):
                member = self.server.get_member(member_id)
                name = member.display_name if member else "*Old Member*"
                entry = f"{index + 1}. {name} has {member_kudos} kudos"
                if member.id == ctx.author.id:
                    entry = f"**{entry}**"
                leader_board.append(entry)

            embed.add_field(
                name="Leader Board", value="\n".join(leader_board), inline=False
            )
        else:
            points_left = self.points_left_to_give(ctx.author.id)
            kudos_to_give = f"{points_left} of {self.pool_size}"
            footer += f" | {kudos_to_give} to give"

        embed.set_footer(text=footer)
        await ctx.send(embed=embed)

    @Cog.listener()
    async def on_raw_reaction_add(self, reaction):
        if not self.settings.get("KUDOS_ENABLED", True):
            return

        if reaction.emoji.id not in self.reactions:
            return

        reacter: nextcord.Member = self.server.get_member(reaction.user_id)
        channel: nextcord.TextChannel = self.server.get_channel(reaction.channel_id)
        message: nextcord.Message = await channel.fetch_message(reaction.message_id)

        # Don't allow kudos in channels the user can't message in unless it's the archive
        if not channel.permissions_for(reacter).send_messages and (
            not channel.category or channel.category.id != 829826306890924083
        ):
            return

        if reacter.bot or message.author.bot:
            return

        if message.author.id == reaction.user_id:
            # Remove all kudos reactions a user tries to give them self
            await self.clear_previous_kudos(message, reaction.member, True)
            return

        level = self.reactions[reaction.emoji.id]
        kudos_left = self.points_left_to_give(reaction.user_id)
        kudos_points = self.point_values[level]

        if -1 < kudos_left < kudos_points:
            await channel.send(
                delete_after=5,
                embed=nextcord.Embed(
                    color=RED,
                    description=f"{reacter.mention} you don't have enough kudos right now",
                ),
            )
            for r in message.reactions:
                if isinstance(r.emoji, str):
                    continue

                kudos_level = self.reactions.get(r.emoji.id, False)
                if kudos_level == level:
                    await r.remove(reacter)
                    break
            return

        await self.clear_previous_kudos(message, reaction.member, level)
        kudos.remove_kudos(reaction.message_id, reaction.user_id)

        kudos.give_user_kudos(
            kudos_points, message.author.id, reaction.user_id, message.id
        )

        multiplier = self.get_pool_multiplier(reaction.member)
        kudos_message = (
            f"{max(0, kudos_left - kudos_points)} of {self.pool_size * multiplier}"
        )
        if multiplier == 0:
            kudos_message = "∞"

        await channel.send(
            embed=nextcord.Embed(
                color=BLUE,
                description=(
                    f"{reacter.mention} gave {message.author.mention} {kudos_points} kudos!"
                ),
            ).set_footer(
                text=f"'!kudos help' or '!kudos leaderboard' | {kudos_message} kudos to give"
            ),
            reference=message,
            allowed_mentions=nextcord.AllowedMentions(replied_user=False),
        )

    @Cog.listener()
    async def on_raw_reaction_remove(self, reaction):
        if self.dev_author and reaction.user_id != self.dev_author:
            return

        if reaction.emoji.id not in self.reactions:
            return

        reacter: nextcord.Member = self.server.get_member(reaction.user_id)
        channel = self.server.get_channel(reaction.channel_id)
        message = await channel.fetch_message(reaction.message_id)

        if not channel.permissions_for(reacter).send_messages:
            return

        if message.author == reaction.user_id and not self.dev_author:
            return

        kudos.remove_kudos(reaction.message_id, reaction.user_id)

    async def clear_previous_kudos(self, message, user, giving):
        for reaction in message.reactions:
            if isinstance(reaction.emoji, str):
                continue

            kudos_level = self.reactions.get(reaction.emoji.id, False)
            if not kudos_level or kudos_level == giving:
                continue

            await reaction.remove(user)

    def points_left_to_give(self, user_id: int):
        member = self.server.get_member(user_id)
        multiplier = self.get_pool_multiplier(member)

        if multiplier == 0:
            return -1  # Infinite kudos

        pool_size = self.pool_size * multiplier

        since = datetime.utcnow() - timedelta(
            minutes=self.pool_regeneration * pool_size
        )
        kudos_given = kudos.get_kudos_given_since(user_id, since)

        if not kudos_given:
            return pool_size

        total_points = pool_size
        last_given = kudos_given[-1][0]
        for given, points in reversed(kudos_given):
            # Regenerate points since the last time they were given
            total_points = min(
                pool_size,
                total_points
                + (given - last_given).seconds // 60 // self.pool_regeneration,
            )
            last_given = given
            # Remove the points given from the pool
            total_points = max(0, total_points - points)

        # Regenerate all points
        total_points = min(
            pool_size,
            total_points
            + (datetime.utcnow() - last_given).seconds // 60 // self.pool_regeneration,
        )

        return total_points

    def get_pool_multiplier(self, member: nextcord.Member) -> int:
        if self.get_role("jedi council") in member.roles:
            return 0  # Infinite kudos
        elif self.get_role("mods") in member.roles:
            return 4
        elif self.get_role("helpers") in member.roles:
            return 2
        return 1


def setup(client):
    client.add_cog(Kudos(client))
