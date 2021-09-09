from beginner.logging import get_logger
from beginner.models.contestants import ContestantInfo
from nextcord.ext import commands
from nextcord.ext.commands import Cog, has_permissions
import nextcord
import requests
from datetime import datetime, timedelta
import os
import asyncio
from urllib.parse import urlparse
import re


class MonthlyShowingOffCog(Cog):
    """Cog for the monthly showing off challenge!"""

    def __init__(self, client):
        self.client = client
        self.log = get_logger(("beginner.py", self.__class__.__name__))
        self.current_month = datetime.today().month
        self.current_year = datetime.today().year
        self.client.loop.call_later(
            self.calculate_time_left(),
            lambda: self.client.loop.create_task(self.send_challenge_message()),
        )

    @property
    def channel(self):
        return self.client.get_channel(
            int(
                os.environ.get("BPY_MONTHLY_SHOWING_OFF_CHANNEL_ID", 836419179779063868)
            )
        )

    @property
    def guild(self):
        return self.channel.guild

    @Cog.listener()
    async def on_ready(self):
        self.log.debug(f"{type(self).__name__} is ready")
        channel_id = os.environ.get("BPY_MONTHLY_SHOWING_OFF_CHANNEL_ID")
        if not channel_id:
            self.log.debug("Channel was not set")

        while not self.channel:
            self.log.debug(
                f"Channel couldn't be found, trying again in 5 seconds ({channel_id!r})"
            )
            await asyncio.sleep(5)

        await self.check_invalid_messages()

    def challenge_message_embed(self):
        github_emoji = nextcord.utils.get(self.channel.guild.emojis, name="github")
        embed = nextcord.Embed(
            color=0xFFE873,
            title="Monthly Project!",
            description=(
                f"Post your projects in this channel for the community to see!\n Below are a few ways to submit your "
                f"project **(one submission only!)**:\n\n**{github_emoji}Github**\n Post your awesome "
                f"project on Github (make sure it is a repository)."
            ),
        )

        embed.add_field(
            name="▶ YT video", value="Post a video on Youtube", inline=False
        )
        embed.add_field(
            name="⛔ Deleting messages",
            value="To delete your submission, react with ⛔",
            inline=False,
        )
        embed.add_field(
            name="🏆 Winner",
            value="In order to win, you must have the most reactions. Winners will be announced monthly",
            inline=False,
        )

        embed.set_author(
            name=self.client.user.display_name,
            icon_url=str(self.client.user.avatar.url),
        )

        embed.set_thumbnail(
            url="https://clipart.world/wp-content/uploads/2020/12/Winner-Trophy-clipart-transparent.png"
        )

        return embed

    @commands.command()
    @has_permissions(administrator=True)
    async def start(self, ctx) -> None:
        start_message = await ctx.send(embed=self.challenge_message_embed())
        await start_message.pin()
        await ctx.message.delete()

    @start.error
    async def err(*args):
        ...

    def calculate_time_left(self):
        """Calculate time left for the next challenge"""
        current_date = datetime.today()
        current_month = current_date.month
        current_year = current_date.year
        last_date = datetime(current_year, current_month + 1, 1, 0, 0, 0)
        return (last_date - current_date).total_seconds()

    async def check_invalid_messages(self):
        """Will iterate over messages while the bot was offline to make sure no incorrectly formatted messages were sent"""
        current_time = datetime.utcnow()
        first_day = datetime.utcnow() - timedelta(hours=0, minutes=10)

        messages = await self.channel.history(
            after=first_day, before=current_time, limit=1000
        ).flatten()

        for message in messages:
            try:
                x = (
                    ContestantInfo.select()
                    .where(message.id == ContestantInfo.bot_message_id)
                    .get()
                )

            except ContestantInfo.DoesNotExist:
                await asyncio.sleep(0.9)
                await message.delete()

            except IndexError:
                pass

    def check_link(self, link):
        try:
            response = requests.get(link).status_code
        except requests.exceptions.ConnectionError:
            return False

        if response == 200:
            return True

    def check_invalid_website(self, website_link: str) -> bool:
        invalid_domains = ["giphy.com", "tenor.com"]
        domain = urlparse(website_link.lower()).netloc
        return domain in invalid_domains

    def create_error_message(self, message, reason):
        embed = nextcord.Embed(
            title="Error!",
            description=f"{message.author.mention} {reason}",
            color=nextcord.Colour.red(),
        )
        return embed

    async def send_challenge_message(self):
        """Send the monthly message to begin the contest"""
        await self.get_message_history()
        await self.channel.send(embed=self.challenge_message_embed())

    @Cog.listener()
    async def on_message(self, message):
        if message.channel != self.channel or message.author.bot:
            return

        await self.scan_link(message)

    def get_author_id(self, bot_message_id):
        """Get the author id from the database by using the message id"""

        try:
            author_id = (
                ContestantInfo.select(ContestantInfo.original_author_id)
                .where(bot_message_id == ContestantInfo.bot_message_id)
                .get()
                .original_author_id
            )
        except IndexError:
            return

        except ContestantInfo.DoesNotExist:
            self.log.error("Contestant was not found")
            return

        return author_id

    def save_message(self, author_id: int, bot_message_id: int) -> None:
        """Saves message data in database"""

        contestant = ContestantInfo(
            original_author_id=author_id,
            bot_message_id=bot_message_id,
        )
        contestant.save()

    def delete_message(self, bot_message_id):
        """Delete message from the database"""
        ContestantInfo.delete().where(bot_message_id == ContestantInfo.bot_message_id)
        self.log.debug("Deleted message successfully")

    def get_link(self, message):
        url = re.findall(
            "(?:(?:https?|ftp):\/\/)?[\w/\-?=%.]+\.[\w/\-&?=%.]+",
            message,
        )
        return "".join(url[0]) if url[0] else None

    async def scan_link(self, message):
        """Check what type of link it is (Github, non-Github, or invalid)"""

        if (
            message.content.startswith("!")
            and message.author.guild_permissions.administrator
        ):
            return
        if "https://" in (content := message.content) and self.check_link(
            self.get_link(content)
        ):
            link = self.get_link(message.content)
            desc = " ".join(message.content.split(link))
            if self.check_invalid_website(content):
                await message.delete()
                await self.channel.send(
                    embed=self.create_error_message(
                        message, "This is a blacklisted link!"
                    ),
                    delete_after=8,
                )
                return

            if "https://github.com" in message.content:
                await self.github_get(message, desc)

            else:
                await message.channel.send(
                    embed=nextcord.Embed(
                        title=f"**{message.author.display_name}**",
                        description=f"Project: {link}\n {desc}",
                        color=nextcord.Colour.green(),
                    ).set_thumbnail(url=message.author.avatar.url)
                )
                await message.delete()

            bot_message_id = self.channel.last_message_id

            self.save_message(message.author.id, bot_message_id)

        else:
            await message.channel.send(
                embed=self.create_error_message(
                    message, "Invalid resource, not a link"
                ),
                delete_after=8,
            )
            await message.delete()

        return

    async def github_get(self, message, desc):
        """Manipulating the url that was sent and converting it into a appropriate url for the api"""
        link = self.get_link(message.content)
        msg = link.split("/")
        try:
            modified_msg = f"https://api.github.com/repos/{msg[3]}/{msg[4]}"
        except IndexError:
            await message.channel.send(
                embed=self.create_error_message(message, "Invalid GitHub link"),
                delete_after=8,
            )
            await message.delete()
            return

        repo_data = requests.get(modified_msg).json()
        await self.github_response(message, repo_data, message.author.id, desc)

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
        """Making an embed for the github response wrapped in a function"""
        git_embed = nextcord.Embed(title=project_name, color=nextcord.Colour.random())

        github_emoji = nextcord.utils.get(self.channel.guild.emojis, name="github")
        git_embed.add_field(
            name="Owner:", value=f"{github_emoji} {owner}", inline=False
        )

        if description:
            print(description)
            git_embed.add_field(
                name="Description:", value=f"```{description}```", inline=False
            )

        git_embed.add_field(name="Language:", value=language, inline=True)
        git_embed.add_field(name="Project Url:", value=project_url, inline=True)
        git_embed.add_field(name="Github profile:", value=profile_url, inline=False)
        git_embed.set_author(
            name=message.author.display_name, icon_url=message.author.avatar.url
        )
        git_embed.set_thumbnail(url=avatar)

        return git_embed

    async def github_response(self, message, json, author_id, desc):
        """Getting the github response and sending the values in an embed, as well as saving it in the db"""
        error = json.get("message")
        print(error)
        error_embed = self.create_error_message(
            message, "Unsuccessful Github response!"
        )

        error_embed.add_field(name="Response:", value=error)

        if error:
            await message.channel.send(embed=error_embed, delete_after=8)
            await message.delete()
            return

        size = json["size"]

        if size == 0:
            await message.channel.send(
                embed=nextcord.Embed(
                    title="Error!",
                    description=f"{message.author.mention} Thats an empty Repository!",
                    color=nextcord.Colour.red(),
                ),
                delete_after=8,
            )
            await message.delete()
            return

        project_name = json["name"]
        owner = json["owner"]["login"]
        avatar = json["owner"]["avatar_url"]
        project_url = json["html_url"]
        description = desc
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

        self.save_message(author_id, bot_message_id)

    async def get_message_history(self):
        """Getting the message history and returning messages that are applicable to the month's challenge. After that
        we are parsing the reactions and id and sending that to get_winners()."""
        votes = []
        users = []

        this_month = datetime.utcnow().replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        last_month = (this_month - timedelta(days=1)).replace(day=1)
        messages = await self.channel.history(
            after=last_month, before=this_month, limit=1000
        ).flatten()
        for message in messages:
            final_reactions = 0
            author_id = self.get_author_id(message.id)

            if self.guild.get_member(author_id):
                for reaction in message.reactions:
                    reaction_authors = await reaction.users().flatten()

                    for reaction_author in reaction_authors:
                        if reaction_author.id != author_id:
                            final_reactions += 1

                votes.append(final_reactions)
                users.append((message.id, final_reactions))

        await self.get_winners(votes, users)

    async def send_default_winner_embed(self, author_project, member):
        """A function that sends an embed if there is single winner"""
        default_winner_embed = nextcord.Embed(
            title=f"🥁 The winner this month is... 🥁",
            description=f"The One & Only: 🎉{member.mention}",
            color=nextcord.Color.orange(),
        )
        default_winner_embed.add_field(
            name="Check out the project:", value=author_project
        )
        wolf_cheer_emoji = nextcord.utils.get(self.guild.emojis, name="wolfcheer")

        default_winner_embed.set_thumbnail(url=wolf_cheer_emoji.url)
        return await self.channel.send(embed=default_winner_embed)

    def multiple_winner_embed(self, winners_string):
        """Simple making the code neater by making a function for making a embed with multiple winners"""

        embed = nextcord.Embed(
            title="🥁 The winners of this month are... 🥁",
            description=winners_string,
            color=nextcord.Color.orange(),
        )

        wolf_cheer_emoji = nextcord.utils.get(
            self.channel.guild.emojis, name="wolfcheer"
        )
        embed.set_thumbnail(url=wolf_cheer_emoji.url)
        return embed

    async def get_multiple_winners(self, winner_ids):
        """A function to get multiple winners if there is an instance of it"""

        winners_string = ""
        winner_projects = []

        winner_details = [
            self.channel.guild.get_member(self.get_author_id(winner_id))
            for winner_id in winner_ids
        ]

        # Iterating to get the url of the project and checking different types of embeds
        for winner_id in winner_ids:
            embed = (await self.channel.fetch_message(winner_id)).embeds[0]
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

    async def get_winners(self, votes, users):
        """A function to check how many winners are there and then sending embeds based on that"""
        max_vote = max(votes)
        winners_votes = votes.count(max_vote)

        # Instance if there is only one winner
        if winners_votes == 1:
            for message_id, votes in users:
                if votes == max_vote:
                    print(message_id, votes)
                    await self.get_single_winner_info(message_id)

        # If there is more than one winner
        elif winners_votes > 1:
            winners = [message_id for message_id, votes in users if votes == max_vote]
            await self.channel.send(
                embed=await self.get_multiple_winners(winners)
            )  # Like i did here

    @Cog.listener()
    async def on_raw_reaction_add(self, payload: nextcord.RawReactionActionEvent):
        """The listener function that will take car of people deleting there own projects if wanted. As well as will
        take care of people wanting to cheat."""
        if payload.channel_id != self.channel.id:
            return

        # Retrieving required data
        author_id = self.get_author_id(payload.message_id)
        payload_author_object = self.channel.guild.get_member(payload.user_id)
        message = await self.channel.fetch_message(payload.message_id)
        has_manage_perms = self.channel.permissions_for(
            payload_author_object
        ).manage_messages
        # Checking if the user wants to delete and checking if someone is trying to cheat
        if payload.emoji.name == "⛔":
            if payload.user_id == author_id or has_manage_perms:
                self.delete_message(payload.message_id)
                await message.delete()
                return

            await message.remove_reaction("⛔", payload_author_object)

        if payload.emoji.name != "⛔" and author_id == payload.user_id:
            await message.remove_reaction(payload.emoji, payload_author_object)


def setup(client):
    client.add_cog(MonthlyShowingOffCog(client))
