from beginner.cog import Cog
from beginner.colors import *
from beginner.models.messages import Message, MessageTypes
from discord import Embed
import re


class RulesCog(Cog):
    def clean_rule(self, rule_content: str):
        return "\n".join(re.findall(r"<p.*?>(.+?)</p>", rule_content))

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
