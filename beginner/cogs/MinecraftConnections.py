from beginner.cog import Cog
import aiohttp
import discord
import discord.ext.commands
from mcstatus import MinecraftServer, MinecraftBedrockServer
from MinePI import MinePI
import datetime
import base64, io, json
class MinecraftConnections(commands.Cog):
    def __init__(self,client):
        self.client = client
        self.beginnerMC="IP"

    @commands.command()
    async def mcinfo(self,ctx, *, user_name):
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
    async def mcstatus(self,ctx):
        online_emoji = discord.utils.get(self.client.emojis, name="Online")
        embed_to_edit = await ctx.send(embed=discord.Embed(title="Searching......Please wait", color=0xffffff))
        try:
            server = MinecraftServer.lookup(self.BeginnerMc)
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

    @commands.Cog.listener()
    async def on_ready(self):
        self.guild = self.client.get_guild(644299523686006834)
def setup(client):
    client.add_cog(MinecraftConnections(client))
