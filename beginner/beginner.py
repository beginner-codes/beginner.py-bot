from aiohttp import ClientSession
from beginner.cog import Cog
from beginner.scheduler import initialize_scheduler
from nextcord import Embed, Webhook
from nextcord.ext import commands
from functools import lru_cache
import nextcord
import os


class BeginnerCog(Cog):
    def __init__(self, client):
        super().__init__(client)
        self.__loaded = False

    @commands.Cog.listener()
    async def on_ready(self):
        self.logger.debug("Cog ready")
        initialize_scheduler(loop=self.client.loop)

        if not BeginnerCog.is_dev_env():
            message = "restarted" if self.__loaded else "is online"
            self.__loaded = True
            await self.get_channel("🤖bot-dev").send(
                f"Bot {message}! Image Version: {os.environ.get('BOT_IMAGE_VERSION', 'NOT SET')}"
            )

    @Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error):
        match error:
            case commands.errors.CommandNotFound():
                return

            case _:
                await self._send_error_to_webhook(error, ctx)

        raise error

    async def _send_error_to_webhook(self, error: Exception, ctx: commands.Context):
        async with ClientSession() as session:
            wh = Webhook.partial(
                882811369353793576,
                self.settings.get("_ERROR_WEBHOOK_URL"),
                session=session,
            )
            await wh.send(
                embed=Embed(
                    title="🛑Error Encountered",
                    description=f"{error}\n\nCommand: {ctx.command and ctx.command.qualified_name or ctx!r}",
                    color=0xFF8800,
                )
            )

    @Cog.listener()
    async def on_message(self, message: nextcord.Message):
        if message.author.bot:
            return

        if self.server.me not in message.mentions:
            return

        if message.reference:
            return

        m: nextcord.Message = await message.channel.send(
            f"Hi {message.author.mention}! I'm the beginner.py bot developed collaboratively by members of this server "
            f"using the nextcord.py package! If you'd like to see my code or even contribute yourself I'm on GitHub "
            f"https://github.com/beginner-codes/beginner.py-bot",
            allowed_mentions=nextcord.AllowedMentions(users=[message.author]),
        )
        await m.edit(suppress=True)

    @Cog.command()
    async def export(self, ctx, namespace):
        if len([r for r in ctx.author.roles if r.id == 644301991832453120]) == 0:
            return

        path = os.path.join("data", f"{namespace}.json")
        if not os.path.exists(path):
            await ctx.send(f"No such namespace: {namespace}")
        else:
            with open(path, "r") as json_file:
                await ctx.send(f"Here you go", file=nextcord.File(json_file))

    @Cog.command(name="import")
    async def import_(self, ctx, namespace):
        if len([r for r in ctx.author.roles if r.id == 644301991832453120]) == 0:
            return

        path = os.path.join("data", f"{namespace}.json")
        if not ctx.message.attachments:
            await ctx.send(f"Nothing attached to import")
        else:
            await ctx.message.attachments[0].save(path)
            self.client.unload_extension(f"beginner.cogs.{namespace}")
            self.client.load_extension(f"beginner.cogs.{namespace}")
            await ctx.send(
                f"Namespace {namespace} updated with contents of {ctx.message.attachments[0].filename}"
            )

    @staticmethod
    @lru_cache()
    def is_dev_env():
        return not os.environ.get("PRODUCTION_BOT", False)


def setup(client):
    client.add_cog(BeginnerCog(client))
