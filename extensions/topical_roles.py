import dippy.labels
import dippy
import discord
import re
from nextcord import (
    ButtonStyle,
    utils,
    Interaction,
    PartialEmoji,
    Message,
    TextChannel,
    Embed,
)
from nextcord.ui import View, button


class AssignTopicsView(View):
    @button(
        emoji=PartialEmoji(name="python", id=934950343614275594),
        label="Python",
        style=ButtonStyle.grey,
        custom_id="assign_python",
    )
    async def assign_python(self, _, interaction: Interaction):
        role = utils.get(interaction.guild.roles, name="python")
        if role not in interaction.user.roles:
            await interaction.user.add_roles(role)
            await interaction.response.send_message(
                "You've been given the Python topical role",
                ephemeral=True,
            )
        else:
            await interaction.user.remove_roles(role)
            await interaction.response.send_message(
                "You've been removed the Python topical role",
                ephemeral=True,
            )

    def __init__(self):
        super().__init__(timeout=None)

    @button(
        emoji=PartialEmoji(name="javascript", id=908457207597764678),
        label="JavaScript",
        style=ButtonStyle.grey,
        custom_id="assign_javascript",
    )
    async def assign_javascript(self, _, interaction: Interaction):
        role = utils.get(interaction.guild.roles, name="javascript")
        if role not in interaction.user.roles:
            await interaction.user.add_roles(role)
            await interaction.response.send_message(
                "You've been given the JavaScript topical role",
                ephemeral=True,
            )
        else:
            await interaction.user.remove_roles(role)
            await interaction.response.send_message(
                "You've been removed the JavaScript topical role",
                ephemeral=True,
            )

    @button(
        emoji=PartialEmoji(name="webdev", id=934956458938880050),
        label="Web Dev",
        style=ButtonStyle.grey,
        custom_id="assign_webdev",
    )
    async def assign_webdev(self, _, interaction: Interaction):
        role = utils.get(interaction.guild.roles, name="webdev")
        if role not in interaction.user.roles:
            await interaction.user.add_roles(role)
            await interaction.response.send_message(
                "You've been given the Web Dev topical role",
                ephemeral=True,
            )
        else:
            await interaction.user.remove_roles(role)
            await interaction.response.send_message(
                "You've been removed the Web Dev topical role",
                ephemeral=True,
            )

    @button(
        emoji=PartialEmoji(name="clang", id=934951942029979688),
        label="C",
        style=ButtonStyle.grey,
        custom_id="assign_clang",
    )
    async def assign_clang(self, _, interaction: Interaction):
        role = utils.get(interaction.guild.roles, name="clang")
        if role not in interaction.user.roles:
            await interaction.user.add_roles(role)
            await interaction.response.send_message(
                "You've been given the C language topical role",
                ephemeral=True,
            )
        else:
            await interaction.user.remove_roles(role)
            await interaction.response.send_message(
                "You've been removed from the C language topical role",
                ephemeral=True,
            )

    @button(
        emoji=PartialEmoji(name="java", id=934957425587523624),
        label="Java",
        style=ButtonStyle.grey,
        custom_id="assign_java",
    )
    async def assign_java(self, _, interaction: Interaction):
        role = utils.get(interaction.guild.roles, name="java")
        if role not in interaction.user.roles:
            await interaction.user.add_roles(role)
            await interaction.response.send_message(
                "You've been given the Java topical role",
                ephemeral=True,
            )
        else:
            await interaction.user.remove_roles(role)
            await interaction.response.send_message(
                "You've been removed the Java topical role",
                ephemeral=True,
            )

    @button(
        emoji="🧠",
        label="Machine Learning",
        style=ButtonStyle.grey,
        custom_id="assign_ml",
    )
    async def assign_ml(self, _, interaction: Interaction):
        role = utils.get(interaction.guild.roles, name="ml")
        if role not in interaction.user.roles:
            await interaction.user.add_roles(role)
            await interaction.response.send_message(
                "You've been given the Machine Learning topical role",
                ephemeral=True,
            )
        else:
            await interaction.user.remove_roles(role)
            await interaction.response.send_message(
                "You've been removed the Machine Learning topical role",
                ephemeral=True,
            )


class TopicalRolesExtension(dippy.Extension):
    client: dippy.Client
    labels: dippy.labels.storage.StorageInterface

    def __init__(self):
        super().__init__()
        self.log_channel = None
        self.topical_roles = {
            "python": "python",
            "py": "python",
            "javascript": "javascript",
            "js": "javascript",
            "webdev": "webdev",
            "java": "java",
            "c": "clang",
            "cpp": "clang",
            "ml": "ml",
        }

    @dippy.Extension.listener("ready")
    async def ready(self):
        self.client.add_view(AssignTopicsView())

    @dippy.Extension.listener("message")
    async def scan_for_dollar_mentions(self, message: Message):
        if not message.guild:
            return

        staff_role = utils.get(message.guild.roles, name="staff")
        if staff_role not in message.author.roles:
            return

        roles = re.findall(
            r"(?:\W|^)\$(" + "|".join(self.topical_roles) + ")(?:\W|$)",
            message.content,
        )
        if roles:
            await message.reply(
                ", ".join(
                    utils.get(
                        message.guild.roles, name=self.topical_roles[mention]
                    ).mention
                    for mention in roles
                ),
                mention_author=False,
            )

    @dippy.Extension.command("!setup topic assignments")
    async def setup_topic_assignments(self, message: Message):
        if not message.author.guild_permissions.administrator:
            return

        channel: TextChannel = message.channel_mentions[0]
        await channel.send(
            embed=Embed(
                title="Topical Roles",
                description=(
                    "Select the topics you're interested in, like, or want to learn."
                    "You may get pinged for useful resources or information related to your selected topics."
                ),
                color=0x306998,
            ),
            view=AssignTopicsView(),
        )
