import nextcord
from nextcord import PartialEmoji
from nextcord.ext import commands

from beginner.cog import Cog
from beginner.models.settings import Settings

from datetime import datetime, timedelta
import os

bump_rate_limits = {}
BUMP_RATE_COOLDOWN = 24


class BuddyCog(Cog):
    def __init__(self, client):
        super().__init__(client)
        self.buddy_view_added = False
        # Replace with your own user id or any user id that's already been used before to submit a buddy form
        self.buddy_form_user_id = 111111111111111111

    @Cog.listener()
    async def on_ready(self):
        await super().on_ready()
        if not self.buddy_view_added:
            self.client.add_view(BuddyFormView(self.buddy_form_user_id))
            self.buddy_view_added = True

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
        self.settings["BUDDY_CATEGORY"] = category.id

    async def get_buddy_chat_category(self) -> int:
        return self.settings["BUDDY_CATEGORY"]

    @Cog.command("buddy")
    @commands.has_permissions(kick_members=True)
    async def create_buddy_chat(
        self,
        ctx: nextcord.ext.commands.Context,
        name: str,
        members: commands.Greedy[nextcord.Member],
    ):
        category = await self.get_buddy_chat_category()

        if not category or ctx.channel.category.id != category:
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

        if not category or ctx.channel.category.id != category:
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

        if not category or ctx.channel.category.id != category:
            return

        if not isinstance(ctx.channel, nextcord.Thread):
            return

        await ctx.channel.add_user(member)

    @Cog.command("rename")
    @commands.has_permissions(kick_members=True)
    async def rename_buddy_chat(self, ctx: nextcord.ext.commands.Context, *, name: str):
        category = await self.get_buddy_chat_category()

        if not category or ctx.channel.category.id != category:
            return

        if not isinstance(ctx.channel, nextcord.Thread):
            return

        await ctx.channel.edit(name=name)

    @Cog.command("close")
    async def close_buddy_chat(self, ctx: nextcord.ext.commands.Context):
        category = await self.get_buddy_chat_category()

        if not category or ctx.channel.category.id != category:
            await ctx.send(
                "You can use the `/close` slash command to close a help post."
            )
            return

        if not ctx.channel.permissions_for(ctx.author).kick_members:
            return

        if not isinstance(ctx.channel, nextcord.Thread):
            return

        await ctx.channel.delete()

    @Cog.command("archive")
    @commands.has_permissions(kick_members=True)
    async def archive_buddy_chat(self, ctx: nextcord.ext.commands.Context):
        category = await self.get_buddy_chat_category()

        if not category or ctx.channel.category.id != category:
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
        buddy_role = nextcord.utils.get(self.server.roles, name="buddy")
        member = self.server.get_member(interaction.user.id)
        if not member or buddy_role not in member.roles:
            await interaction.send(
                "Sorry! You require the buddy achievement role to use this feature.",
                ephemeral=True,
            )
            return

        await interaction.response.send_modal(LookForBuddy())


class LookForBuddy(nextcord.ui.Modal):
    def __init__(self):
        super().__init__(
            title="Looking For Buddy",
            timeout=None,
        )

        self.looking_for_buddy_channel_id = int(
            os.environ.get("LOOKING_FOR_BUDDY_CHANNEL_ID", 987390245207150663)
        )

        self.pl_options = {
            "Python": PartialEmoji(name="python", id=934950343614275594),
            "Javascript": PartialEmoji(name="javascript", id=908457207597764678),
            "TypeScript": PartialEmoji(name="typescript", id=982974090400923689),
            "C": PartialEmoji(name="clang", id=934951942029979688),
            "C#": PartialEmoji(name="c_sharp", id=947603932161667132),
            "C++": PartialEmoji(name="cpp", id=947603931519926342),
            "Java": PartialEmoji(name="java", id=934957425587523624),
            "PHP": "🐘",
            "GDScript": "🕹️",
            "Other": "🧑‍💻",
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

        self.region_options = {
            "North America": "🌎",
            "South America": "🌎",
            "Europe": "🌍",
            "Africa": "🌍",
            "Central Asia": "🌏",
            "East Asia": "🌏",
            "Oceania": "🌏",
        }
        self.region = nextcord.ui.Select(
            placeholder="Region",
            options=[
                nextcord.SelectOption(label=name, emoji=emoji)
                for name, emoji in self.region_options.items()
            ],
        )
        self.add_item(self.region)

        # The number of choices in select options is limited to a max of 25.
        # https://discord.com/developers/docs/interactions/message-components#select-menu-object-select-menu-structure
        age_options = [nextcord.SelectOption(label=str(i)) for i in range(13, 37)] + [
            nextcord.SelectOption(label="37+")
        ]
        self.age_range = nextcord.ui.Select(
            placeholder="Age Range (Optional) - Select min and max",
            options=age_options,
            min_values=0,
            max_values=2,
        )
        self.add_item(self.age_range)

        self.looking_for = nextcord.ui.TextInput(
            label="Looking For:",
            style=nextcord.TextInputStyle.paragraph,
            placeholder="Accountability and somebody to share ideas with",
            max_length=150,
        )
        self.add_item(self.looking_for)

    async def callback(self, interaction: nextcord.Interaction):
        embed = nextcord.Embed(
            title=self.title,
            timestamp=datetime.now(),
        )
        embed.add_field(name="Username:", value=interaction.user.mention, inline=False)
        embed.add_field(
            name="Programming Languages:",
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
        user_region = self.region.values[0]
        embed.add_field(
            name="Region:",
            value=f"{self.region_options[user_region]} {user_region}",
            inline=True,
        )

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

        looking_for_buddy_channel = interaction.guild.get_channel(
            self.looking_for_buddy_channel_id
        )
        await looking_for_buddy_channel.send(
            embed=embed, view=BuddyFormView(interaction.user.id)
        )
        await interaction.send(
            f"Your buddy form has been submitted to {looking_for_buddy_channel.mention}.",
            ephemeral=True,
        )


class BuddyFormView(nextcord.ui.View):
    def __init__(self, user_id) -> None:
        super().__init__(timeout=None)
        self.user_id = user_id

    @nextcord.ui.button(
        emoji=PartialEmoji(name="beginner~1", id=669941641292808202),
        style=nextcord.ButtonStyle.blurple,
        label="Bump",
        custom_id="BuddyBumpButton",
    )
    async def bump_buddy_form(self, _, interaction: nextcord.Interaction):
        now = datetime.utcnow()
        delta = now - bump_rate_limits.get(interaction.user.id, now)
        if timedelta(hours=0) < delta < timedelta(hours=BUMP_RATE_COOLDOWN):
            await interaction.response.send_message(
                f"{interaction.user.mention}, you can only bump once a day! You have {BUMP_RATE_COOLDOWN-(delta.seconds//(60*60))} hour(s) left.",
                ephemeral=True,
            )
            return
        bump_rate_limits[interaction.user.id] = now

        await interaction.message.delete()
        embed = interaction.message.embeds[0]
        if not embed.footer.text:
            embed.set_footer(
                text=f"Bumped 1 time by {interaction.user.display_name}.",
            )
        else:
            footer_text = embed.footer.text.split()
            bump_count = int(footer_text[1])
            embed.set_footer(
                text=f"Bumped {bump_count + 1} times, most recently by {interaction.user.display_name}.",
            )
        await interaction.channel.send(
            embed=embed, view=BuddyFormView(interaction.user.id)
        )

        bumped_user = interaction.client.get_user(self.user_id)
        is_self_bump = (bumped_user == interaction.user)
        await interaction.channel.send(
            f"""{interaction.user.mention}, you bumped {[bumped_user.mention, "your"][is_self_bump]}{"'s" * (not is_self_bump)} buddy submission!""",
            delete_after=4,
        )

    @nextcord.ui.button(
        emoji="🗑️",
        style=nextcord.ButtonStyle.red,
        label="Delete",
        custom_id="DeleteBuddyPost",
    )
    async def delete_buddy_post(self, _, interaction: nextcord.Interaction):
        if interaction.user.id != self.user_id:
            return

        await interaction.message.delete()
        await interaction.response.send_message(
            f"{interaction.user.mention}, your post has been deleted.",
            ephemeral=True,
        )


def setup(client):
    client.add_cog(BuddyCog(client))
