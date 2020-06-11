from beginner.cog import Cog
from beginner.beginner import BeginnerCog
from beginner.models.messages import Message, MessageTypes
from beginner.options import get_option, set_option
from discord import Embed, Message as DiscordMessage, TextChannel
from discord.ext import commands
import re


class RulesCog(Cog):
    def get_rules_channel(self) -> TextChannel:
        if BeginnerCog.is_dev_env():
            return self.get_channel("empty-channel-for-bot-dev")
        return self.get_channel("rules")

    @property
    def allow_rule_rebuilds(self) -> bool:
        return get_option("allow-rule-rebuilds", True)

    @allow_rule_rebuilds.setter
    def allow_rule_rebuilds(self, value: bool):
        set_option("allow-rule-rebuilds", value)

    def clean_rule(self, rule_content: str):
        return "\n".join(re.findall(r"<p.*?>(.+?)</p>", rule_content))

    @Cog.command(name="rule-updates")
    async def rule_updates(self, ctx, on_or_off: str = ""):
        if not ctx.author.guild_permissions.manage_guild:
            return

        if on_or_off == "":
            await ctx.send(
                f"Rule updates are currently turned {'on' if self.allow_rule_rebuilds else 'off'}."
            )
        elif on_or_off.lower() in {"on", "yes", "true", "t", "y", "1"}:
            self.allow_rule_rebuilds = True
            await ctx.send(f"Rule updates turned on.")
        elif on_or_off.lower() in {"off", "no", "false", "f", "n", "0"}:
            self.allow_rule_rebuilds = False
            await ctx.send(f"Rule updates turned off.")
        else:
            await ctx.send(f"I don't understand. Rule update setting unchanged.")

    @Cog.command(name="create-rule")
    async def create_rule(self, ctx, *, content):
        if not ctx.author.guild_permissions.manage_guild:
            return

        sections = content.split("\n")
        rule_number = sections[0]
        title = sections[1]
        labels = [label.strip() for label in sections[2].split(", ")]
        rule = "\n".join(sections[3:])

        existing_rule = self.get_rule(rule_number)
        if existing_rule:
            await ctx.send(
                f"There is already a rule #{rule_number} ({existing_rule.title})"
            )

        else:
            new_rule = Message(
                title=f"Rule #{rule_number} - {title}",
                label=" ".join([rule_number] + labels),
                message=rule,
                message_type=MessageTypes.RULE.name,
                author=ctx.author.display_name,
            )
            new_rule.save()

            await ctx.send(
                f"Created rule successfully\n"
                f"Rule #: {rule_number}\n"
                f"Title: {title}\n"
                f"Labels: {', '.join(labels)}\n"
                f"Rule: {rule}"
            )
            await self.rebuild_rule_messages()

    @Cog.command(name="edit-rule")
    async def edit_rule(self, ctx, rule_number, *_):
        if not ctx.author.guild_permissions.manage_guild:
            return

        rule = RulesCog.get_rule(rule_number)
        if rule:
            existing_number = rule.title[
                rule.title.find("#") + 1 : rule.title.find("-") - 1
            ]
            existing_title = rule.title[rule.title.find("-") + 2 :]
            existing_labels = rule.label.split(" ")[1:]
            await ctx.send(
                "Found this rule\n"
                f"**- Rule #:** {existing_number}\n"
                f"**- Title:** {existing_title}\n"
                f"**- Labels:** {', '.join(existing_labels)}\n"
                f"**- Rule:** {rule.message}\n\n"
                "You can enter your changes now\n"
                "Send 'cancel' to stop\n"
                "Use `-` to not change the corresponding field.\n"
                "*Rule #, Title, Labels, Rule Message* should all be on their "
                "own line and in that order."
            )
            message = await self.client.wait_for(
                "message",
                check=lambda msg: msg.channel == ctx.message.channel
                and msg.author == ctx.author,
            )
            if message.content.strip().lower() == "cancel":
                await ctx.send("Canceled, didn't change anything")
                return

            sections = message.content.split("\n")

            rule_number = sections[0]
            title = sections[1]
            labels = [label.strip() for label in sections[2].split(", ")]
            rule_message = "\n".join(sections[3:])

            if rule_number != "-":
                existing_number = rule_number
            if title != "-":
                existing_title = title
            if sections[2] != "-":
                existing_labels = labels
            if rule_message != "-":
                rule.message = rule_message

            rule.title = f"Rule #{existing_number} - {existing_title}"
            rule.label = " ".join([existing_number] + existing_labels)
            rule.author = ctx.author.display_name
            rule.save()

            await ctx.send(
                "Here is the updated rule", embed=self.build_rule_embed(rule)
            )
            await self.rebuild_rule_messages()

    @Cog.command(name="rule")
    async def show_rule(self, ctx, label=None, *_):
        rule = RulesCog.get_rule(label, fuzzy=True)
        if rule:
            await ctx.send(embed=self.build_rule_embed(self.clean_rule(rule)))
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

    def build_rule_embed(self, rule):
        return Embed(description=rule.message, color=0x306998).set_author(
            name=rule.title, icon_url=self.server.icon_url
        )

    async def create_rule_messages(self):
        channel = self.get_rules_channel()
        await channel.send(
            embed=Embed(
                description="Welcome to beginner.py! We hope you'll enjoy your stay and learn "
                "a lot about python with us.\n\n"
                "You'll need to **read through the rules** real quick and "
                "**acknowledge that you've understood them** at the bottom before "
                "you can gain full access to the server.",
                color=0x306998,
            ).set_author(name="Beginner.py Rules", icon_url=self.server.icon_url)
        )
        for rule in sorted(
            self.get_rules(), key=lambda r: int(r.label[: r.label.find(" ")])
        ):
            await channel.send(
                embed=Embed(description=rule.message, color=0x306998).set_author(
                    name=rule.title
                )
            )

    async def rebuild_rule_messages(self):
        if self.allow_rule_rebuilds:
            await self.get_rules_channel().purge(limit=1000)
            await self.create_rule_messages()

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

    @staticmethod
    def sanitize_label(label: str):
        return (
            label.lower().translate({ord("-"): " ", ord("_"): " "}) if label else label
        )


def setup(client):
    client.add_cog(RulesCog(client))
