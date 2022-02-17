from beginner.cog import Cog
from urllib.parse import urlparse
import nextcord
import os


class ChallengeReminderView(nextcord.ui.View):
    @nextcord.ui.button(
        emoji="🔔",
        style=nextcord.ButtonStyle.blurple,
        custom_id="ChallengeReminderButton",
    )
    async def add_reminder_role(self, _, interaction: nextcord.Interaction):
        guild = interaction.guild
        role = nextcord.utils.get(guild.roles, name="Challenges")
        await interaction.response.send_message(
            f"{interaction.user.mention} you will be tagged for new challenges",
            ephemeral=True,
        )
        if role in interaction.user.roles:
            return

        await interaction.user.add_roles(role)

    @nextcord.ui.button(
        emoji="🚫",
        style=nextcord.ButtonStyle.grey,
        custom_id="StopChallengeReminderButton",
    )
    async def remove_reminder_role(self, _, interaction: nextcord.Interaction):
        guild = interaction.guild
        role = nextcord.utils.get(guild.roles, name="Challenges")
        await interaction.response.send_message(
            f"{interaction.user.mention} you will no longer be tagged for new challenges",
            ephemeral=True,
        )
        if role not in interaction.user.roles:
            return

        await interaction.user.remove_roles(role)


class Challenges(Cog):
    def __init__(self, client):
        super().__init__(client)
        self.challenge_reminder_added = False
        self.approved_hosts = [
            "gist.github.com",
            "paste.pythonnextcord.com",
            "hastebin.com",
            "pastebin.com",
            "github.com",
        ]

    @Cog.listener()
    async def on_ready(self):
        if not self.challenge_reminder_added:
            self.client.add_view(ChallengeReminderView(timeout=None))
            self.challenge_reminder_added = True

    @Cog.listener()
    async def on_message(self, message):
        await self.challenge_alerts(message)
        await self.challenge_submission_scan(message)

    async def challenge_alerts(self, message: nextcord.Message):
        if message.channel != self.get_channel(
            os.environ.get("DAILY_CHALLENGE_CHANNEL", "🏋weekday-challenges")
        ):
            return

        if message.author.bot:
            return

        role = nextcord.utils.get(message.guild.roles, name="Challenges")
        await message.delete()
        announcement = await message.channel.send(
            f"**{role.mention}{message.content.removeprefix('**Challenge')}",
            view=ChallengeReminderView(timeout=None),
        )
        await announcement.publish()

    async def challenge_submission_scan(self, message):
        if message.author.bot:
            return

        if (
            not message.channel.topic
            or "challenge submissions" not in message.channel.topic.casefold()
        ):
            return

        content = message.content
        if content.startswith("http"):
            parsed = urlparse(content)
            if parsed.netloc.lower().replace("www.", "") in self.approved_hosts:
                return

        elif content.startswith("||") and content.endswith("||"):
            return

        await message.delete()
        await message.channel.send(
            content=f"{message.author.mention}",
            embed=nextcord.Embed(
                description=(
                    f"All code submissions must be either shared on an approved site or must be enclosed in spoiler"
                    f"tags\n\n**Approved Sites**\n"
                    + (
                        "\n".join(
                            f"- [{host}](https://{host})"
                            for host in self.approved_hosts
                        )
                    )
                    + "\n\n**Formatting Code**\nProper code formatting doesn't support spoilers, so all you need to"
                    " do is put your code inside of spoiler tags, formatting isn't required.\n"
                    "**Example**\n```md\n||your code\ngoes in\nhere||\n```"
                ),
                color=0xCC2222,
            ).set_author(
                name="Spoiler Free Code Submissions Only",
                icon_url=self.server.icon.url,
            ),
            delete_after=30,
        )

    @Cog.command()
    async def codehosts(self, ctx):
        await ctx.send(
            embed=nextcord.Embed(
                description=(
                    f"These are the code file hosts we recommend for sharing code:\n"
                    + (
                        "\n".join(
                            f"- [{host}](https://{host})"
                            for host in self.approved_hosts
                        )
                    )
                ),
                color=0x306998,
            ).set_author(
                name="Recommended Code File Hosts",
                icon_url=self.server.icon.url,
            )
        )


def setup(client):
    client.add_cog(Challenges(client))
