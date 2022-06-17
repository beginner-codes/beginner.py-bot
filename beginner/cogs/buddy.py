import nextcord
from nextcord.ext import commands

from beginner.cog import Cog
from beginner.models.settings import Settings

from datetime import datetime


class BuddyCog(Cog):
    @Cog.command("set-buddychat-category")
    @commands.has_permissions(kick_members=True)
    async def set_buddy_chat_category_command(
        self, ctx: nextcord.ext.commands.Context, category: nextcord.CategoryChannel
    ):
        if not category:
            await ctx.send(f"Couldn't find a category named {category!r}.")
            return

        await self.set_buddy_chat_category(category)

        await ctx.send(f"Set {category} as the buddy chat category.")

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
    async def create_buddy_chat(
        self,
        ctx: nextcord.ext.commands.Context,
        name: str,
        members: commands.Greedy[nextcord.Member],
    ):
        category = await self.get_buddy_chat_category()

        if not category or ctx.channel.category.name != category:
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
                color=0x00FF66,
            )
        )
        await welcome_msg.pin()

    @Cog.command("remove")
    @commands.has_permissions(kick_members=True)
    async def remove_buddy(
        self, ctx: nextcord.ext.commands.Context, member: nextcord.Member
    ):
        category = await self.get_buddy_chat_category()

        if not category or ctx.channel.category.name != category:
            return

        if not isinstance(ctx.channel, nextcord.Thread):
            return

        await ctx.channel.remove_user(member)

    @Cog.command("add")
    @commands.has_permissions(kick_members=True)
    async def add_buddy(
        self, ctx: nextcord.ext.commands.Context, member: nextcord.Member
    ):
        category = await self.get_buddy_chat_category()

        if not category or ctx.channel.category.name != category:
            return

        if not isinstance(ctx.channel, nextcord.Thread):
            return

        await ctx.channel.add_user(member)

    @Cog.command("rename")
    @commands.has_permissions(kick_members=True)
    async def rename_buddy_chat(self, ctx: nextcord.ext.commands.Context, *, name: str):
        category = await self.get_buddy_chat_category()

        if not category or ctx.channel.category.name != category:
            return

        if not isinstance(ctx.channel, nextcord.Thread):
            return

        await ctx.channel.edit(name=name)

    @Cog.command("close")
    @commands.has_permissions(kick_members=True)
    async def close_buddy_chat(self, ctx: nextcord.ext.commands.Context):
        category = await self.get_buddy_chat_category()

        if not category or ctx.channel.category.name != category:
            return

        if not isinstance(ctx.channel, nextcord.Thread):
            return

        await ctx.channel.delete()

    @Cog.command("archive")
    @commands.has_permissions(kick_members=True)
    async def archive_buddy_chat(self, ctx: nextcord.ext.commands.Context):
        category = await self.get_buddy_chat_category()

        if not category or ctx.channel.category.name != category:
            return

        if not isinstance(ctx.channel, nextcord.Thread):
            return

        members = await ctx.channel.fetch_members()
        for member in members:
            await ctx.channel.remove_user(member)

        await ctx.channel.edit(name=f"{ctx.channel.name}-archive")
        await ctx.channel.send("🗂 This channel has been archived")

    @Cog.slash_command(
        name="look-for-buddy",
        description="Look for a buddy",
    )
    async def look_for_buddy(self, interaction: nextcord.Interaction):
        await interaction.response.send_modal(LookForBuddy())


class LookForBuddy(nextcord.ui.Modal):
    def __init__(self):
        super().__init__(
            title="Looking For Buddy",
            timeout=None,
        )

        self.pl_options = {
            "Python": "🐍",
            "Javascript": "🤖",
            "C": "🤖",
            "Java": "🤖",
        }
        self.programming_languages = nextcord.ui.Select(
            placeholder="Programming Languages",
            options=[
                nextcord.SelectOption(label=name, emoji=emoji)
                for name, emoji in self.pl_options.items()
            ],
            min_values=1,
            max_values=len(self.pl_options),
        )
        self.add_item(self.programming_languages)

        self.current_projects = nextcord.ui.TextInput(
            label="Current Projects",
            style=nextcord.TextInputStyle.paragraph,
            placeholder="Simple website",
            max_length=150,
        )
        self.add_item(self.current_projects)

        tz_options = [
            nextcord.SelectOption(label=f"UTC{'+' if i>=0 else ''}{i}")
            for i in range(-11, 12)
        ]
        self.timezone = nextcord.ui.Select(placeholder="Timezone", options=tz_options)
        self.add_item(self.timezone)

        # The number of choices in select options is limited to a max of 25.
        # https://discord.com/developers/docs/interactions/message-components#select-menu-object-select-menu-structure
        age_options = [nextcord.SelectOption(label=str(i)) for i in range(13, 37)] + [
            nextcord.SelectOption(label="37+")
        ]
        self.age_range = nextcord.ui.Select(
            placeholder="Age Range (Optional)",
            options=age_options,
            min_values=0,
            max_values=2,
        )
        self.add_item(self.age_range)

        self.looking_for = nextcord.ui.TextInput(
            label="Looking For:",
            style=nextcord.TextInputStyle.paragraph,
            placeholder="Accountability and somebody to share ideas with",
            max_length=50,
        )
        self.add_item(self.looking_for)

    async def callback(self, interaction: nextcord.Interaction):
        embed = nextcord.Embed(
            title=self.title,
            timestamp=datetime.now(),
        )
        embed.add_field(name="Username:", value=interaction.user.mention, inline=False)
        embed.add_field(
            name="Programming Languages",
            value="\n".join(
                [f"{self.pl_options[i]} {i}" for i in self.programming_languages.values]
            ),
            inline=False,
        )
        embed.add_field(
            name="Current Projects:",
            value=f"```{self.current_projects.value}```",
            inline=False,
        )
        embed.add_field(name="Timezone:", value=self.timezone.values[0], inline=True)

        if self.age_range.values:
            embed.add_field(
                name="Age Range:",
                value="-".join(i for i in self.age_range.values)
                if len(self.age_range.values) > 1
                else self.age_range.values[0],
                inline=True,
            )

        embed.add_field(
            name="Looking for:", value=f"```{self.looking_for.value}```", inline=False
        )
        embed.set_author(name=interaction.user, icon_url=interaction.user.avatar)
        embed.set_thumbnail(url=interaction.user.avatar)

        await interaction.send(embed=embed)


def setup(client):
    client.add_cog(BuddyCog(client))
