from beginner.logging import get_logger
from beginner.models.contestants import ContestantInfo
from discord.ext.commands import Cog
import discord
import requests
from datetime import datetime, timedelta
import os


class MonthlyShowingOffCog(Cog):
    """Cog for the monthly showing off challenge!"""

    def __init__(self, client):
        self.client = client
        self.log = get_logger(("beginner.py", self.__class__.__name__))
        self.channel_id = 836419179779063868
        self.current_month = datetime.today().month
        self.current_year = datetime.today().year
        self.client.loop.call_later(
            self.calculate_time_left(),
            lambda: self.client.loop.create_task(self.send_challenge_message()),
        )

    @property
    def channel(self):
        return self.client.get_channel(
            os.environ.get("BPY_MONTHLY_SHOWING_OFF_CHANNEL_ID", 836419179779063868)
        )

    @Cog.listener()
    async def on_ready(self):
        self.log.debug(f"{type(self).__name__} is ready")

    def calculate_time_left(self):
        """Calculate time left for the next challenge"""
        current_date = datetime.today()
        current_month = current_date.month
        current_year = current_date.year
        last_date = datetime(current_year, current_month + 1, 1, 0, 0, 0)
        return (last_date - current_date).seconds

    def cog_unload(self):
        self.send_challenge_message.cancel()

    async def send_challenge_message(self):
        """Send the monthly message to begin the contest"""
        channel = self.client.get_channel(836419179779063868)

        embed = discord.Embed(
            color=0xFFE873,
            title="Monthly Project!",
            description="Post you projects in this channel for the community to see!\n Below are few ways to submit the project **(one submssion only!)**:\n\n**<:github:837128482097332225>Github**\n Post your awesome project on Github.(make sure it is a repository)",
        )

        embed.add_field(
            name="▶ YT video", value="Post a video on Youtube", inline=False
        )

        embed.set_author(
            name=self.client.user.display_name,
            icon_url=self.client.user.default_avatar_url,
        )

        embed.set_thumbnail(
            url="https://clipart.world/wp-content/uploads/2020/12/Winner-Trophy-clipart-transparent.png"
        )
        await self.get_message_history()
        await channel.send(embed=embed)

    @Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        await self.scan_link(message)

    def get_author_id(self, bot_message_id):
        """Get the author id from the database by using the message id"""
        return (
            ContestantInfo.select(ContestantInfo.original_author_id)
            .where(bot_message_id == ContestantInfo.bot_message_id)
            .get()
            .original_author_id
        )

    def delete_message(self, bot_message_id):
        """Delete message from the database"""
        ContestantInfo.delete().where(bot_message_id == ContestantInfo.bot_message_id)
        print("Deleted successfully")

    async def scan_link(self, message):
        """Check what type of link it is (Github, non-Github or invalid)"""
        if message.channel != self.channel:
            return
        # Embed for normal and valid link
        default_embed = discord.Embed(
            title=f"**{message.author.name}**",
            description=f"Project: {message.content}",
            color=discord.Colour.green(),
        )

        error_embed = discord.Embed(
            title=f"Error!",
            description=f"{message.author.mention} Invalid recources, Not a link!",
            colour=discord.Colour.red(),
        )

        default_embed.set_thumbnail(url=message.author.avatar_url)
        if "https://" in message.content:
            author_id = message.author.id
            time_sent = message.created_at.strftime("%Y-%m")
            if "https://github.com" in message.content:
                await self.github_get(message)

            else:
                await message.channel.send(embed=default_embed)
                await message.delete()

            bot_message_id = self.channel.last_message_id
            contestant = ContestantInfo(
                original_author_id=author_id,
                bot_message_id=bot_message_id,
                datetime=time_sent,
            )
            contestant.save()

        else:
            await message.channel.send(embed=error_embed, delete_after=8)
            await message.delete()

        return

    async def github_get(self, message):
        """      Manipulating the url that was sent and converting it into a appropriate url for the api     """
        msg = message.content.split("/")
        try:
            modified_msg = f"https://api.github.com/repos/{msg[3]}/{msg[4]}"
        except:
            await message.channel.send(
                embed=discord.Embed(
                    title="Error!",
                    description=f"{message.author.mention} Invalid github link!",
                    color=discord.Colour.red(),
                ),
                delete_after=8,
            )
            await message.delete()
            return

        repo_data = requests.get(modified_msg).json()
        await self.github_response(
            message, repo_data, message.author.id, message.created_at
        )

    def parse_git_to_embed(
        self,
        project_name,
        owner,
        avatar,
        profile_url,
        description,
        project_url,
        language,
        message,
    ):
        """Making an embed for the githup response wrapped in a function"""
        git_embed = discord.Embed(title=project_name, color=discord.Colour.random())

        git_embed.add_field(
            name="Owner:", value=f"<:github:837128482097332225> {owner}", inline=False
        )

        if description:
            git_embed.add_field(
                name="Description:", value=f"```{description}```", inline=False
            )

        git_embed.add_field(name="Language:", value=language, inline=True)
        git_embed.add_field(name="Project Url:", value=project_url, inline=True)
        git_embed.add_field(name="Github profile:", value=profile_url, inline=False)
        git_embed.set_author(
            name=message.author.name, icon_url=message.author.avatar_url
        )
        git_embed.set_thumbnail(url=avatar)

        return git_embed

    async def github_response(self, message, json, author_id, time_sent):
        """Getting the github response and sending the values in an embed, as well as saving it in the db"""
        error = json.get("message", bool(""))

        error_embed = discord.Embed(
            title="Error!",
            description=f"{message.author.mention} Unsucessful Github response!",
            color=discord.Colour.red(),
        )
        error_embed.add_field(name="Response:", value=error)

        if error:
            await message.channel.send(embed=error_embed, delete_after=8)
            await message.delete()
            return

        size = json["size"]

        if size == 0:
            await message.channel.send(
                embed=discord.Embed(
                    title="Error!",
                    description=f"{message.author.mention} Thats an empty Repository!",
                    color=discord.Colour.red(),
                ),
                delete_after=8,
            )
            await message.delete()
            return

        project_name = json["name"]
        owner = json["owner"]["login"]
        avatar = json["owner"]["avatar_url"]
        project_url = json["html_url"]
        description = json["description"]
        profile_url = json["owner"]["html_url"]
        language = json["language"]

        git_embed = self.parse_git_to_embed(
            project_name,
            owner,
            avatar,
            profile_url,
            description,
            project_url,
            language,
            message,
        )

        await message.channel.send(embed=git_embed)
        await message.delete()

        bot_message_id = self.channel.last_message_id
        contestant = ContestantInfo(
            original_author_id=author_id,
            bot_message_id=bot_message_id,
            datetime=time_sent,
        )
        contestant.save()

    async def get_message_history(self):
        """Getting the message history and returning messages that are applicable to the month's challenge. After that
        we are parsing the reactions and id and sending that to get_winners()."""
        votes = []
        users = []
        channel = self.client.get_channel(836419179779063868)
        this_month = datetime.utcnow().replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        last_month = (this_month - timedelta(days=1)).replace(day=1)
        messages = await channel.history(
            after=last_month, before=this_month, limit=1000
        ).flatten()
        for message in messages:
            reaction_count = sum(reaction.count for reaction in message.reactions)
            votes.append(reaction_count)
            users.append((message.id, reaction_count))

        await self.get_winners(votes, users)

    async def send_default_winner_embed(self, author_project, member):
        """A function that sends an embed if there is single winner"""
        default_winner_embed = discord.Embed(
            title=f"🥁 The winner of this month is... 🥁",
            description=f"One and Only: 🎉{member.mention}",
            color=discord.Color.orange(),
        )
        default_winner_embed.add_field(
            name="Check out the project:", value=author_project
        )
        default_winner_embed.set_thumbnail(
            url="https://cdn.discordapp.com/emojis/711749954837807135.png?v=1"
        )
        return await self.channel.send(embed=default_winner_embed)

    def multiple_winner_embed(self, winners_string):
        """Simple making the code neater by makign a function for making a embed with multiple winners"""

        embed = discord.Embed(
            title="🥁 The winners of this month are... 🥁",
            description=winners_string,
            color=discord.Color.orange(),
        )

        embed.set_thumbnail(
            url="https://cdn.discordapp.com/emojis/711749954837807135.png?v=1"
        )
        return embed

    async def get_multiple_winners(self, winner_ids):
        """A function to get multiple winners if there is an instance of it"""

        winners_string = ""
        winner_projects = []

        try:  # Getting winner objects with a try block just in case the db doesnt have the person
            winner_details = [
                self.channel.guild.get_member(self.get_author_id(id))
                for id in winner_ids
            ]

        except ContestantInfo.DoesNotExist:
            print("Unable to return users")
            return

        # Iterating to get the url of the project and checking different types of embeds
        for id in winner_ids:
            embed = (await self.channel.fetch_message(id)).embeds[0]
            if embed.fields:
                winner_projects.append(
                    [embed.fields[2].value, embed.fields[3].value][
                        len(embed.fields) == 5
                    ]
                )
            else:
                winner_projects.append(embed.description[9:])

        # Last step to zip the user with the project url and concatenate them to a string
        for winner, project in zip(winner_details, winner_projects):
            winners_string += f"👑{winner.mention}   {project}\n"

        return self.multiple_winner_embed(winners_string)

    async def get_single_winner_info(self, message_id):
        """A function to get the winner's info and send the embed to the channel"""
        try:
            winner_id = self.get_author_id(message_id)
            member = self.channel.guild.get_member(winner_id)
            winner_project = await self.channel.fetch_message(message_id)
            winner_project_details = winner_project.embeds[0]
            winner_project_url = (
                [
                    winner_project_details.fields[2].value,
                    winner_project_details.fields[3].value,
                ][len(winner_project_details.fields) == 5]
                if bool(len(winner_project_details.fields))
                else winner_project_details.description[9:]
            )
            await self.send_default_winner_embed(winner_project_url, member)
        except IndexError:
            pass
        except ContestantInfo.DoesNotExist:
            print("Contestant was not found")

    async def get_winners(self, votes, users):
        """A function to check how many winners are there and then sending embeds based on that"""
        max_vote = max(votes)
        winners_votes = votes.count(max_vote)

        # Instance if there is only one winner
        if winners_votes == 1:
            for message_id, votes in users:
                if votes == max_vote:
                    await self.get_single_winner_info(message_id)

        # If there is more than one winner
        elif winners_votes > 1:
            winners = [message_id for message_id, votes in users if votes == max_vote]
            await self.channel.send(
                embed=await self.get_multiple_winners(winners)
            )  # Like i did here

    @Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        """The listener function that will take car of people deleting there own projects if wanted. As well as will
        take care of people wanting to cheat."""
        if payload.channel_id != self.channel.id:
            return

        # Retrieving required data
        author_id = self.get_author_id(payload.message_id)
        payload_author_object = self.channel.guild.get_member(payload.user_id)
        message = await self.channel.fetch_message(payload.message_id)

        # Checking if the user wants to delete and checking if someone is trying to cheat
        if payload.emoji.name == "⛔":
            if payload.user_id == author_id:
                self.delete_message(payload.message_id)
                await message.delete()
                return

            await message.remove_reaction("⛔", payload_author_object)

        if payload.emoji.name != "⛔" and author_id == payload.user_id:
            await message.remove_reaction(payload.emoji, payload_author_object)


def setup(client):
    client.add_cog(MonthlyShowingOffCog(client))
