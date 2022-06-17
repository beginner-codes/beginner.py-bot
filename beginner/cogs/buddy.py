from discord import Member
from beginner.cogs.settings import Settings
import nextcord
from nextcord.ext import commands

from beginner.cog import Cog
from beginner.models.settings import Settings


class BuddyCog(Cog):
#    def __init__(self, client):
#        super().__init__(client)

    @Cog.listener()
    async def on_ready(self):
        category = await self.get_buddy_chat_category()
        print(type(category))
        print(category)


    @Cog.command("set-buddychat-category")
    @commands.has_permissions(kick_members=True)
    async def set_buddy_chat_category_command(
        self, ctx: nextcord.ext.commands.Context, category: nextcord.CategoryChannel
    ):
        if not category:
            await ctx.send(f"Couldn't find a category named {category!r}.")
            return
    
        await self.set_buddy_chat_category(category)

        await ctx.send(
            f"Set {category} as the buddy chat category."
        )

    async def set_buddy_chat_category(self, category: nextcord.CategoryChannel):
        buddy_category = Settings(
            name="BUDDY_CATEGORY",
            value=category,
        )
        buddy_category.save()

    async def get_buddy_chat_category(self) -> str:
        category = Settings.select().where(Settings.name == "BUDDY_CATEGORY").get()
        return category.value


    @Cog.command("buddy")
    @commands.has_permissions(kick_members=True)
    async def create_buddy_chat(self, ctx: nextcord.ext.commands.Context, name: str, members: commands.Greedy[nextcord.Member]):
        category = await self.get_buddy_chat_category()

        if not category or ctx.channel.category == category:
            return

        thread = await ctx.channel.create_thread(name=name)
        for member in members:
            await thread.add_user(member)

        welcome_msg = await thread.send(
            embed=nextcord.Embed(
                title=f"Welcome to your buddy chat!",
                description=(
                    "**Recommended Structure**\n"
                    "**Daily**\n"
                    "Check in, talk about what you've been working on and any struggles.\n"
                    "**Weekly**\n"
                    "Set goals for the week, review them. Have you achieved your goals? If not, why not?\n"
                    "\n"
                    "**Goal Ideas**\n"
                    "- Start a new project.\n"
                    "- Start learning a new language.\n"
                    "- Implemenent a new feature in your project.\n"
                    "- Spent at least two hours a day programming.\n"
                ),
                color=0x00FF66
            )
        )
        await welcome_msg.pin()


def setup(client):
    client.add_cog(BuddyCog(client))
