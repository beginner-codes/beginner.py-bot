from beginner.cog import Cog
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
            "Keep It Friendly": (
                "Be courteous and understanding. We're friends here and we're all working towards being better "
                "programmers."
            ),
            "Keep It Legal": (
                "We can't judge what your goals are. So we ask that you not ask about or discuss  anything that "
                "violates any laws or that breaks the terms of service (ToS) for any app/service/program/etc. If "
                "you're not sure __please ask__, we don't mind."
            ),
            "Getting Help": (
                "If you have a question ask it, someone will answer. Please don't ask to DM. This prevents others from "
                "being able to contribute and it makes it impossible for us to ensure you get the highest quality help."
            ),
            "Finally": (
                "It should go without saying: flaming, trolling, spamming, and harassing, along with racism and "
                "bigotry of any kind towards any group or individual is strictly prohibited and will be dealt with "
                "appropriately."
            )
        }

    def clean_rule(self, rule_content: str):
        return "\n".join(re.findall(r"<p.*?>(.+?)</p>", rule_content))

    async def ready(self):
        rules: discord.TextChannel = discord.utils.get(self.server.channels, name="rules")
        messages = await rules.history(limit=1).flatten()
        if not messages:
            message = await rules.send(
                embed=self.build_rule_message_embed(
                    "Rules, Guidlines, & Conduct",
                    (
                        "Welcome!!! We're happy to have you! Please give these rules and guidelines a quick read and "
                        "then hit the ✅ to gain access to the rest of the server."
                    )
                )
            )
            await message.add_reaction("✅")

            rules = discord.utils.get(self.server.channels, name="server-rules")
            await rules.send(
                embed=self.build_rule_message_embed(
                    "Rules, Guidlines, & Conduct",
                    ""
                )
            )

    def build_rule_message_embed(self, title: str, message: str) -> discord.Embed:
        admin: discord.Member = self.server.get_member(266432511897370625)
        embed = Embed(
            title=title,
            description=message,
            timestamp=datetime(2020, 8, 31, 0, 0, 0, 0, pytz.timezone("US/Eastern")),
            color=BLUE
        )
        embed.set_footer(text=admin.name, icon_url=admin.avatar_url)

        for field_title, field_content in self.message_fields.items():
            embed.add_field(
                name=field_title,
                value=field_content,
                inline=False
            )

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
    async def show_formatting_rule(self, ctx, language: str = "py", *, _=None):
        await ctx.send(
            embed=(
                Embed(
                    title="Code Formatting",
                    description=f"When sharing code with the community, please use the correct formatting for ease of readability.",
                    color=BLUE
                )
                    .add_field(
                    name="Example",
                    value=(
                        f"\\`\\`\\`{language}\n"
                        f"YOUR CODE HERE\n"
                        f"\\`\\`\\`\n\n"
                        f"*Those are back ticks not single quotes, typically the key above `TAB`*"
                    ),
                    inline=False
                )
                    .set_thumbnail(url=ctx.guild.icon_url)
            )
        )

    def build_rule_embed(self, rule):
        return Embed(description=self.clean_rule(rule.message), color=0x306998).set_author(
            name=rule.title, icon_url=self.server.icon_url
        )

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
