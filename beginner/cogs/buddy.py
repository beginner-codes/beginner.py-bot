from beginner.cogs.settings import Settings
import nextcord
from nextcord.ext import commands

from beginner.cog import Cog
from beginner.models.settings import Settings


class BuddyCog(Cog):
    def __init__(self, client):
        super().__init__(client)

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


def setup(client):
    client.add_cog(BuddyCog(client))
