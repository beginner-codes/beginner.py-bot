from beginner.logging import get_logger
from beginner.models.contestants import ContestantInfo
from discord.ext import tasks, commands
from discord.ext.commands import Cog, Context, command
import discord
import requests
from datetime import datetime, timedelta


class MonthlyShowingOffCog(Cog):
    """   Cog for the monthly showing off challenge!   """

    def __init__(self, client):
        self.client = client
        self.log = get_logger(("beginner.py", self.__class__.__name__))
        self.channel_id = 836419179779063868
        self.channel = None
        self.current_month = datetime.today().month
        self.current_year = datetime.today().year
        self.client.loop.call_later(self.calculate_time_left(), lambda:self.client.loop.create_task(self.send_challenge_message()))
        
    @Cog.listener()
    async def on_ready(self):
        self.log.debug(f"{type(self).__name__} is ready")
        self.channel = self.client.get_channel(self.channel_id)
    
    def calculate_time_left(self):
        """   Calculate time left for the next challenge   """
        current_date = datetime.today()
        current_month = current_date.month
        current_year = current_date.year 
        last_date = datetime(current_year,current_month +1,1, 0, 0, 0)
        return (last_date - current_date).seconds
        
    def cog_unload(self):
        self.send_challenge_message.cancel()

    async def send_challenge_message(self):
        """   Send the monthly message to begin the contest   """
        channel = self.client.get_channel(836419179779063868)

        embed = discord.Embed(color = 0xFFE873,
            title = 'Monthly Project!',
            description = 'Post you projects in this channel for the community to see!\n Below are few ways to submit the project **(one submssion only!)**:\n\n**<:github:837128482097332225>Github**\n Post your awesome project on Github.(make sure it is a repository)'
            )

        embed.add_field(
            name = "▶ YT video",
            value = "Post a video on Youtube",
            inline = False)  

        embed.set_author(
            name = self.client.user.display_name,
            icon_url = self.client.user.default_avatar_url)

        embed.set_thumbnail(url = 'https://clipart.world/wp-content/uploads/2020/12/Winner-Trophy-clipart-transparent.png')
        await self.get_message_history()
        await channel.send(embed = embed)

    @Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        await self.scan_link(message)

    def get_author_id(self,bot_message_id):
        """   Get the author id from the database by using the message id   """
        return ContestantInfo.select(ContestantInfo.original_author_id).where(bot_message_id == ContestantInfo.bot_message_id).get().original_author_id

    def delete_message(self, bot_message_id):
        """   Delete message from the database   """
        ContestantInfo.delete().where(bot_message_id == ContestantInfo.bot_message_id)
        print("Deleted successfully")

    async def scan_link(self, message):
        """   Check what type of link it is(Github, non-Github or invalid)   """
        if message.channel.id != self.channel_id:
            return
        #Embed for normal and valid link
        default_embed = discord.Embed(
            title = f"**{message.author.name}**",
            description = f"Project: {message.content}",
            color = discord.Colour.green()
        )
        
        error_embed = discord.Embed(
            title = f"Error!",
            description = f"{message.author.mention} Invalid recources, Not a link!",
            colour = discord.Colour.red()
        )

        default_embed.set_thumbnail(url = message.author.avatar_url)
        if "https://" in message.content:
            author_id = message.author.id
            time_sent = message.created_at.strftime("%Y-%m")
            if "https://github.com" in message.content: 
                await self.github_get(message) 
                
            else:
                await message.channel.send(embed = default_embed)
                await message.delete()
            
            bot_message_id = self.channel.last_message_id
            contestant = ContestantInfo(
                original_author_id = author_id,
                bot_message_id = bot_message_id,
                datetime = time_sent
                )
            contestant.save()
                
        else: 
            await message.channel.send(embed = error_embed, delete_after = 8)
            await message.delete()
        
        return 

    async def github_get(self, message):
        """      Manipulating the url that was sent and converting it into a appropriate url for the api     """
        msg = message.content.split('/')
        try:
            modified_msg = f"https://api.github.com/repos/{msg[3]}/{msg[4]}"
        except:
            await message.channel.send(embed = discord.Embed(title = "Error!", description = f"{message.author.mention} Invalid github link!", color = discord.Colour.red()), delete_after = 8)
            await message.delete()
            return

        repo_data = requests.get(modified_msg).json()
        await self.github_response(message, repo_data, message.author.id, message.created_at)
    
    def  parse_git_to_embed(self, project_name, owner, avatar, profile_url, description, project_url, language, message):
        """        Making an embed for the githup response wrapped in a funciton         """ 
        git_embed = discord.Embed(
            title = project_name,
            color = discord.Colour.random()
        )

        git_embed.add_field(name = "Owner:", value = f"<:github:837128482097332225> {owner}",  inline = False)
        
        if description:
            git_embed.add_field(name = "Description:", value = f"```{description}```",  inline = False)

        git_embed.add_field(name = "Language:", value = language,  inline = True)
        git_embed.add_field(name = "Project Url:", value = project_url,  inline = True) 
        git_embed.add_field(name = "Github profile:", value = profile_url,  inline = False) 
        git_embed.set_author(name = message.author.name, icon_url = message.author.avatar_url)
        git_embed.set_thumbnail(url= avatar)

        return git_embed


    async def github_response(self, message, json, author_id, time_sent):
        """      Getting the github response and sending the values in an embed, as well as saving it in the db      """
        error = json.get("message", bool(""))

        error_embed = discord.Embed(
            title = "Error!", 
            description = f"{message.author.mention} Unsucessful Github response!",
            color = discord.Colour.red()
        )
        error_embed.add_field(name = "Response:", value = error)

        if error:
            await message.channel.send(embed = error_embed, delete_after = 8)
            await message.delete()
            return

        size = json['size']