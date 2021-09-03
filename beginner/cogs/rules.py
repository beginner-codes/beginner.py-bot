from beginner.cog import Cog, commands
from beginner.colors import *
from beginner.models.messages import Message, MessageTypes
from datetime import datetime
from nextcord import Embed
import re
import nextcord.utils
import pytz


class RulesCog(Cog):
    def __init__(self, client: nextcord.Client):
        super().__init__(client)
        self.message_fields = {
            "No DMing others or asking others DM you": {
                "description": (
                    "A lot of scammers use DMs as a way to propagate dangerous code. So to ensure the safety of our "
                    "members and to ensure the highest quality of help we do not permit anyone to ask members to DM."
                ),
                "labels": ("dm", "dming", "pm"),
            },
            "No solicitation": {
                "description": (
                    "This is a beginner server not a job board. We're here to learn not find unnecessary products/tools"
                    "/services. *If you share an affiliate link be up front about that.*"
                ),
                "labels": (
                    "solicitation",
                    "advert",
                    "advertising",
                    "ads",
                    "ad",
                    "jobs",
                    "job",
                ),
            },
            "No discussion of anything that violates laws or any ToS": {
                "description": (
                    "We cannot judge your intent. As such we do not allow discussion of anything that could be in "
                    "violation of laws or the terms of service/use for any product or service. If there isn't official "
                    "documentation on how to do something you're not likely going to find much help here."
                ),
                "labels": ("tos", "hacker", "illegal", "hack", "hacking"),
            },
            "No unreadable display names or inappropriate names/avatars": {
                "description": (
                    "Your display name should be readable (not invisible or illegible), reasonably inoffensive, and "
                    "should not contain any words or phrases that could be consider rude or that may look/sound like "
                    "something that is.\n\nYour avatar image/PFP should be reasonably inoffensive."
                ),
                "labels": ("nickname", "avatar", "name", "pfp", "username"),
            },
            "No Harassment, NSFW content, flaming/trolling, or bigotry": {
                "description": (
                    "It should go without saying: flaming, trolling, spamming, and harassing, along with racism and "
                    "bigotry of any kind towards any group or individual is strictly prohibited and will be dealt with "
                    "appropriately."
                ),
                "labels": (
                    "nsfw",
                    "trolling",
                    "harassment",
                    "bigotry",
                    "harassing",
                    "racism",
                ),
            },
            "Finally": {
                "description": (
                    "To ensure everyone can participate and that the server staff can foster an environment amenable "
                    "to growth and learning, please only use __English__. Be kind, courteous, and understanding."
                ),
                "labels": ("finally",),
            },
        }

    @Cog.command(name="update-rules")
    @commands.has_guild_permissions(manage_channels=True)
    async def update_rules_message(self, ctx, *, reason: str):
        rules: nextcord.TextChannel = nextcord.utils.get(
            self.server.channels, name="rules"
        )
        messages = await rules.history(limit=1, oldest_first=True).flatten()
        if messages:
            await messages[0].edit(
                embed=self.build_rule_message_embed(
                    "Rules, Guidlines, & Conduct",
                    (
                        "Welcome!!! We're happy to have you! Please give these rules and guidelines a quick read!"
                    ),
                ),
                allowed_mentions=nextcord.AllowedMentions(
                    everyone=False, users=False, roles=False
                ),
            )
            await rules.send(
                f"Rules message has been updated: {reason}", delete_after=60
            )

    def build_rule_message_embed(self, title: str, message: str) -> nextcord.Embed:
        admin: nextcord.Member = self.server.get_member(266432511897370625)
        embed = Embed(
            title=title,
            description=message,
            timestamp=datetime(2020, 8, 31, 0, 0, 0, 0, pytz.timezone("US/Eastern")),
            color=BLUE,
        )
        embed.set_footer(text=admin.name, icon_url=admin.avatar_url)

        for field_title, field_content in self.message_fields.items():
            embed.add_field(
                name=field_title, value=field_content["description"], inline=False
            )

        return embed

    @Cog.command(name="rule")
    async def show_rule(self, ctx, label=None, *_):
        rule = self.get_rule(label, fuzzy=True)
        if rule:
            await ctx.send(embed=self.build_rule_embed(rule))
        else:
            rules = self.get_rules(label, force=True)
            rule_primary_labels = [
                "**" + self.message_fields[rule]["labels"][0] + "**" for rule in rules
            ]
            await ctx.send(
                embed=Embed(
                    title=(
                        f"Didn't find a rule for '{label}'"
                        if label
                        else "Beginner.py Rules"
                    ),
                    description=f"Here are some rules you might try:\n{', '.join(rule_primary_labels)}"
                    if label
                    else f"Here are all the rules: \n{', '.join(sorted(rule_primary_labels))}",
                    color=0x306998,
                ).set_thumbnail(url=ctx.guild.icon.url)
            )

    @Cog.command(name="formatting", aliases=("format", "code"))
    async def show_formatting_rule(self, ctx, raw_language: str = "py", *, _=None):
        language = "".join(re.findall(r"[a-z0-9]+", raw_language, re.I))
        await ctx.send(
            embed=(
                Embed(
                    title="Code Formatting",
                    description=(
                        "When sharing code with the community, please use the correct formatting for ease of "
                        "readability."
                    ),
                    color=BLUE,
                )
                .add_field(
                    name="Example",
                    value=(
                        f"\\`\\`\\`{language}\n"
                        f"YOUR CODE HERE\n"
                        f"\\`\\`\\`\n\n"
                        f"*Those are back ticks not single quotes, typically the key above `TAB`*"
                    ),
                    inline=False,
                )
                .set_thumbnail(url=ctx.guild.icon.url)
            )
        )

    def build_rule_embed(self, rule):
        return Embed(
            title=rule,
            description=self.message_fields[rule]["description"],
            color=0x306998,
        ).set_thumbnail(url=self.server.icon.url)

    def get_rule(self, label, fuzzy=False):
        for rule_name, rule_info in self.message_fields.items():
            if label.casefold() in rule_info["labels"]:
                rule = rule_name
                break
        else:
            rule = None
        if not rule and fuzzy:
            rules = self.get_rules(label)
            if len(rules) == 1:
                rule = rules[0]
        return rule

    def get_rules(self, label=None, force=True):
        if label:
            rules = [
                rule_name
                for rule_name in self.message_fields
                if label in "".join(rule_name)
            ]
        else:
            rules = self.message_fields
        return rules if rules or not force else self.get_rules(force=False)


def setup(client):
    client.add_cog(RulesCog(client))
