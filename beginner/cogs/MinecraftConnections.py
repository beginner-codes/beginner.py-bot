from discord.ext import commands
import discord
import aiohttp
from mcstatus import MinecraftServer, MinecraftBedrockServer
from MinePI import MinePI
import datetime
import base64, io, json
from googleapiclient.discovery import build as google
from urllib.parse import quote_plus
from random import choice
class MinecraftConnections(commands.Cog):
    def __init__(self,client):
        self.client = client
        self.colors = [0xEA4335, 0x4285F4, 0xFBBC05, 0x34A853]

    @commands.command()
    async def mcinfo(self,ctx, *, user_name):
        if ctx.channel.id != self.bot_channel.id and not ctx.author.guild_permissions.administrator:
            await ctx.send(f"Use this command in the {self.bot_channel.mention} channel",delete_after=10)
            return
        async with ctx.typing():
            try:
                online_emoji = discord.utils.get(self.client.emojis, name="Online")
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"https://api.mojang.com/users/profiles/minecraft/{user_name}") as r:
                        get_uuid = await r.json()
                        uuid = get_uuid["id"]
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"https://api.mojang.com/user/profiles/{uuid}/names") as r:
                        get_name_history = await r.json()
                list = []
                list.append(f"**Original Name: {get_name_history[0]['name']}**")
                for x in range(1, len(get_name_history)):
                    date = f"at {datetime.datetime.utcfromtimestamp(get_name_history[x].get('changedToAt') // 1000).strftime('%Y-%m-%d')}" if \
                        get_name_history[x].get('changedToAt') else None
                    list.append(f"Changed to: **{get_name_history[x]['name']}** {date if date else None}")
                name_history = "\n".join(list)
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"https://sessionserver.mojang.com/session/minecraft/profile/{uuid}") as r:
                        skin_cap = await r.json()
                skin_array = skin_cap["properties"][0]["value"]
                skin_array = json.loads((base64.b64decode(skin_array)))
                skin_url = skin_array["textures"]["SKIN"]["url"]
                Cape_url = skin_array["textures"]["CAPE"]["url"] if "CAPE" in skin_array["textures"] else None
                Embed_Cap_url = f"[Click here to download]({Cape_url})" if Cape_url != None else "User have no Capes"

                async def rander_skin():
                    im = await MinePI.render_3d_skin(user_name)
                    bytes = io.BytesIO()
                    im.save(bytes, 'PNG')
                    bytes.seek(0)
                    return bytes

                file = discord.File(await rander_skin(), 'skin.png')
                embed = discord.Embed(title=f"{online_emoji}Minecraft Java account info of {user_name}:",
                                      colour=0xf4c2c2,
                                      timestamp=ctx.message.created_at)
                embed.set_image(url='attachment://skin.png')
                embed.add_field(name=f"Name History of {user_name}:", value=name_history)
                embed.add_field(name="Links for Skin and Cape(If any):",
                                value=f"Skin Texture: [Click here to download]({skin_url})\nCape Texture: {Embed_Cap_url}",
                                inline=False)
                embed.set_thumbnail(url=f"{skin_url if Cape_url == None else Cape_url}")
                embed.set_footer(text=f"This command only supports Java. Requested by {ctx.author.display_name}")
                await ctx.send(embed=embed, file=file)
            except:
                await ctx.send(
                    embed=discord.Embed(title="Account not found", timestamp=ctx.message.created_at).set_image(
                        url="https://lh3.googleusercontent.com/_UgsPsrxvB8Wd-sFqd7iScBb_iX30SqrgLJ2cg_MqPY7r6OyZjCdEs-6nGxWLHO75YKONNYTtjLIgnoB_vESUjE02JbyzhDg3BE=s400"
                    ).set_footer(
                        text=f"This command only supports Java.\nRequested by {ctx.author.display_name}"
                    )
                )

    @mcinfo.error
    async def mcinfo_error(self,ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("you need to do !mcinfo (MC Java account username)", delete_after=10)
    @commands.command()
    async def online(self,ctx, arg):
        if ctx.channel.id != self.bot_channel.id and not ctx.author.guild_permissions.administrator:
            await ctx.send(f"Use this command in the {self.bot_channel.mention} channel",delete_after=10)
            return
        online_emoji = discord.utils.get(self.client.emojis, name="Online")
        embed_to_edit = await ctx.send(embed=discord.Embed(title="Searching......Please wait", color=0xffffff))
        try:
            server = MinecraftServer.lookup(arg)
            async with ctx.typing():
                status =await server.async_status()
                try:
                    latency = f"{server.ping()}ms"
                except:
                    latency = "Unknown"
                try:
                    version = status.version.name
                except:
                    version = "unknown"
                try:
                    players_online = status.players.online
                except:
                    players_online = "unknown"
                try:
                    players_max = status.players.max
                except:
                    players_max = "unknown"
                try:
                    motd = status.description
                except:
                    motd = None
                try:
                    server_query = server.query()
                except:
                    server_query = None
                java_embed = discord.Embed(title=f"{online_emoji}Status of {arg}:(Java)",
                                           description=f"Server is Online with a latency of {latency}\nSupportedVersions:\n{version}",
                                           colour=0x48a14d)
                java_embed.set_author(name="MineZone",icon_url="https://cdn.discordapp.com/attachments/850019796014858280/868516287167496242/frame_26_delay-0.01s.jpg")
                java_embed.add_field(name="Online",
                                     value=f"There are {players_online} players online out of {players_max}",
                                     inline=False)
                if (motd if type(motd) is not dict else motd['text']).strip() and motd != None:
                    java_embed.add_field(name="Description", value=motd if type(motd) is not dict else motd['text'],
                                         inline=False)
                if server_query:
                    java_embed.add_field(name="Player list",
                                         value=f"{','.join(server_query.players.names if len(server_query.players.names) <= 50 else server_query.players.names[:50])}",
                                         inline=False)
            await embed_to_edit.edit(embed=java_embed)
        except ConnectionRefusedError:
            try:
                server = MinecraftBedrockServer.lookup(arg)
                async with ctx.typing():
                    bedrock =await server.async_status()
                    try:bedrock_latency=bedrock.latency
                    except:bedrock_latency="Unknown"
                    bedrock_embed = discord.Embed(title=f"{online_emoji}Status of {arg}:(Bedrock)",
                                                  description=f"Server is Online with a latency of {round(bedrock_latency*100)}ms\nRunning on {bedrock.map}",
                                                  colour=0x48a14d)
                    bedrock_embed.add_field(name="Online", value=f"There are {bedrock.players_online} online players out of {bedrock.players_max} max players",inline=False)
                    if bedrock.motd :
                        bedrock_embed.add_field(name="Description", value=bedrock.motd)
                await embed_to_edit.edit(embed=bedrock_embed)
            except ConnectionResetError:
                await embed_to_edit.edit(embed=discord.Embed(
                    description="The server you chose dont allow third party fetchers",
                    colour=0xf9423a))
        except:
            await embed_to_edit.edit(embed=discord.Embed(description="The server you chose is either not online , don't exist or don't use the regular Minecraft server protocols",colour=0xf9423a))
    @online.error
    async def online_error(self,ctx,error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("you need to do !online (ip) eg: play.nethergames.net)",delete_after=10)

    @commands.command(aliases=["wiki"])
    async def mcwiki(self, ctx, *, query):
        if ctx.channel.id != self.bot_channel.id and not ctx.author.guild_permissions.administrator:
            await ctx.send(f"Use this command in the {self.bot_channel.mention} channel",delete_after=10)
            return
        async with ctx.typing():
            color = choice(self.colors)
            url_search = (
                f"https://www.google.com/search?hl=en&q={quote_plus(query)}"
                "&btnG=Google+Search&tbs=0&safe=on"
            )
            message = await ctx.send(
                embed=self.create_google_message(
                    f"Searching...\n\n[More Results]({url_search})", color
                )
            )
            query_obj = google(
                "customsearch",
                "v1",
                developerKey="AIzaSyBzmxAhFaj5hRNjW7IppPXGYdN5m_bht2Q",
            )
            query_result = (
                query_obj.cse()
                    .list(
                    q=query,
                    cx="f9026cceb2d7420a2",
                    num=5,
                )
                    .execute()
            )

        results = []
        for result in query_result.get("items", []):
            title = result["title"]
            if len(title) > 77:
                title = f"{title[:77]}..."
            results.append(f"{len(results) + 1}. [{title}]({result['link']})\n")
        await message.edit(
            embed=self.create_google_message(
                f"Results for \"{query}\"\n\n{''.join(results)}\n[More Results]({url_search})",
                color,
            )
        )

    def create_google_message(self, message, color):
        return discord.Embed(description=message, color=color).set_author(
            name=f"Minecraft wiki result", icon_url=self.guild.icon_url
        ).set_thumbnail(
            url="https://cdn.discordapp.com/attachments/850019796014858280/867928608201662554/2021-07-22-180514.gif"
        )

    @mcwiki.error
    async def mcwiki_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("you need to do !mcwiki (your search term))", delete_after=10)

    @commands.Cog.listener()
    async def on_ready(self):
        self.guild = self.client.get_guild(844231449014960160)
        self.bot_channel = self.bump_channel = discord.utils.get(self.guild.text_channels, name="🤖〢bot-commands")
def setup(client):
    client.add_cog(MinecraftConnections(client))