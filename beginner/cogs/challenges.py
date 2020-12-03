from beginner.cog import Cog
from urllib.parse import urlparse
import discord
import os


class Challenges(Cog):
    def __init__(self, client):
        super().__init__(client)
        self.approved_hosts = [
            "gist.github.com",
            "paste.pythondiscord.com",
            "hastebin.com",
            "pastebin.com",
        ]

    @Cog.listener()
    async def on_message(self, message):
        await self.challenge_alerts(message)
        await self.challenge_submission_scan(message)

    async def challenge_alerts(self, message):
        if message.channel != self.get_channel(
                os.environ.get("DAILY_CHALLENGE_CHANNEL", "daily-challenges")
        ):
            return

        if message.author.bot:
            return

        await message.add_reaction("🔔")

    async def challenge_submission_scan(self, message):
        if message.author.bot:
            return

        if "challenge submissions" not in message.channel.topic.casefold():
            return

        content = message.content
        if content.startswith("http"):
            parsed = urlparse(content)
            if parsed.netloc.lower() in self.approved_hosts:
                return

        elif content.startswith("||") and content.endswith("||"):
            return

        await message.delete()
        await message.channel.send(
            content=f"{message.author.mention}",
            embed=discord.Embed(
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
                icon_url=self.server.icon_url,
            ),
            delete_after=30,
        )

    @Cog.listener()
    async def on_raw_reaction_add(self, reaction):
        if reaction.emoji.name != "🔔":
            return

        channel = self.get_channel(
            os.environ.get("DAILY_CHALLENGE_CHANNEL", "daily-challenges")
        )
        if reaction.channel_id != channel.id:
            return

        member = self.server.get_member(reaction.user_id)
        if member.bot:
            return

        if self.get_role("challenges") not in member.roles:
            await self.add_challenges_role(member, channel)
        else:
            await channel.send(
                f"{member.mention} you're already signed up for new challenge notifications", delete_after=5
            )

    async def add_challenges_role(self, member, channel):
        await member.add_roles(self.get_role("challenges"))
        await channel.send(
            f"{member.mention} you will be tagged for new challenges", delete_after=10
        )

    async def remove_challenges_role(self, member, channel):
        await member.remove_roles(self.get_role("challenges"))
        await channel.send(
            f"{member.mention} you will no longer be tagged for new challenges",
            delete_after=10,
        )

    @Cog.listener()
    async def on_raw_reaction_remove(self, reaction):
        if reaction.emoji.name != "🔔":
            return

        channel = self.get_channel(
            os.environ.get("DAILY_CHALLENGE_CHANNEL", "daily-challenges")
        )
        if reaction.channel_id != channel.id:
            return

        member = self.server.get_member(reaction.user_id)
        if member.bot:
            return

        if self.get_role("challenges") in member.roles:
            await self.remove_challenges_role(member, channel)

    @Cog.command()
    async def codehosts(self, ctx):
        await ctx.send(
            embed=discord.Embed(
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
                name="Recommended Code File Hosts", icon_url=self.server.icon_url,
            )
        )


def setup(client):
    client.add_cog(Challenges(client))
