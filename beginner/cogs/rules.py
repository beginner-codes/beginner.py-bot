from beginner.cog import Cog, commands
from beginner.colors import *
from beginner.models.messages import Message, MessageTypes
from datetime import datetime
from discord import Embed
import re
import discord.utils
import pytz


class RulesCog(Cog):
    def __init__(self, client: discord.Client):
        super().__init__(client)
        self.message_fields = {
            "No DMing others or asking others DM you": (
                "A lot of scammers use DMs as a way to propagate dangerous code. So to ensure the safety of our "
                "members and to ensure the highest quality of help we do not permit anyone to ask members to DM."
            ),
            "No solicitation": (
                "This is a beginner server not a job board. We're here to learn not find unnecessary products/tools/"
                "services. *If you share an affiliate link be up front about that.*"
            ),
            "No discussion of anything that violates laws or any ToS": (
                "We cannot judge your intent. As such we do not allow discussion of anything that could be in "
                "violation of laws or the terms of service/use for any product or service. If there isn't official "
                "documentation on how to do something you're not likely going to find much help here."
            ),
            "No unreadable display names or inappropriate names/avatars": (
                "Your display name should be readable (not invisible or illegible), reasonably inoffensive, and should "
                "not contain any words or phrases that could be consider rude or that may look/sound like something "
                "that is.\n\n"
                "Your avatar image/PFP should be reasonably inoffensive."
            ),
            "No Harassment, NSFW content, flaming/trolling, or bigotry": (
                "It should go without saying: flaming, trolling, spamming, and harassing, along with racism and "
                "bigotry of any kind towards any group or individual is strictly prohibited and will be dealt with "
                "appropriately."
            ),
            "Finally": (
                "To ensure everyone can participate and that the server staff can foster an environment amenable to "
                "growth and learning, please only use __English__. Be kind, courteous, and understanding."
            ),
        }

    def clean_rule(self, rule_content: str):
        return "\n".join(re.findall(r"<p.*?>(.+?)</p>", rule_content))

    @Cog.command(name="update-rules")
    @commands.has_guild_permissions(manage_channels=True)
    async def update_rules_message(self, ctx, *, reason: str):
        rules: discord.TextChannel = discord.utils.get(
            self.server.channels, name="rules"
        )
        messages = await rules.history(limit=1, oldest_first=True).flatten()
        if messages:
            await messages[0].edit(
                embed=self.build_rule_message_embed(
                    "Rules, Guidlines, & Conduct",
                    (
                        "Welcome!!! We're happy to have you! Please give these rules and guidelines a quick read! Once "
                        "you're done react to this message to gain access to the rest of the server."
                    ),
                ),
                allowed_mentions=discord.AllowedMentions(
                    everyone=False, users=False, roles=False
                ),
            )
            await rules.send(
                f"Rules message has been updated: {reason}", delete_after=60
            )

    def build_rule_message_embed(self, title: str, message: str) -> discord.Embed:
        admin: discord.Member = self.server.get_member(266432511897370625)
        embed = Embed(
            title=title,
            description=message,
            timestamp=datetime(2020, 8, 31, 0, 0, 0, 0, pytz.timezone("US/Eastern")),
            color=BLUE,
        )
        embed.set_footer(text=admin.name, icon_url=admin.avatar_url)

        for field_title, field_content in self.message_fields.items():
            embed.add_field(name=field_title, value=field_content, inline=False)

        return embed

    @Cog.command(name="rule")
    async def show_rule(self, ctx, label=None, *_):
        rule = RulesCog.get_rule(label, fuzzy=True)
        if rule:
            await ctx.send(embed=self.build_rule_embed(rule))
        else:
            rules = RulesCog.get_rules(label, force=True)
            rule_primary_labels = [
                "**" + rule.label.split(" ")[1] + "**" for rule in rules
            ]
            await ctx.send(
                embed=Embed(
                    description=f"Here are some rules you might try:\n{', '.join(rule_primary_labels)}"
                    if label
                    else f"Here are all the rules: \n{', '.join(sorted(rule_primary_labels))}",
                    color=0x306998,
                ).set_author(
                    name=f"Didn't find a rule for '{label}'"
                    if label
                    else "Beginner.py Rules",
                    icon_url=self.server.icon_url,
                )
            )

    @Cog.command(name="formatting", aliases=("format", "code"))
    async def show_formatting_rule(self, ctx, raw_language: str = "py", *, _=None):
        language = "".join(re.findall(r"[a-z0-9]+", raw_language, re.I))
        await ctx.send(
            embed=(
                Embed(
                    title="Code Formatting",
                    description=f"When sharing code with the community, please use the correct formatting for ease of readability.",
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
                .set_thumbnail(url=ctx.guild.icon_url)
            )
        )

    def build_rule_embed(self, rule):
        return Embed(
            description=self.clean_rule(rule.message), color=0x306998
        ).set_author(name=rule.title, icon_url=self.server.icon_url)

    @staticmethod
    def get_rule(label, fuzzy=False):
        rule = Message.get_or_none(
            (Message.message_type == MessageTypes.RULE.name)
            & (Message.label.startswith(label))
        )
        if not rule and fuzzy:
            rules = RulesCog.get_rules(label)
            if len(rules) == 1:
                rule = rules[0]
        return rule

    @staticmethod
    def get_rules(label=None, force=True, order_by=Message.label.asc()):
        where = Message.message_type == MessageTypes.RULE.name
        if label:
            where &= Message.label.contains(f"%{label}%")
        query = Message.select().where(where)
        rules = query.order_by(order_by).execute()
        return rules if rules or not force else RulesCog.get_rules(force=False)


def setup(client):
    client.add_cog(RulesCog(client))
