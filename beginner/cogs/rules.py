from beginner.cog import Cog, commands
from beginner.colors import *
from datetime import datetime
from nextcord import Embed
import re
import nextcord.utils
import pytz


class RulesCog(Cog):
    def __init__(self, client: nextcord.Client):
        super().__init__(client)
        self.message_fields = {
            "Keep Discussion On the Server": {
                "description": (
                    "Don’t DM members, don’t ask members about DMing. We have help channels if you want an "
                    "uninterrupted space to discuss your questions. This helps ensure you get quality help, that no "
                    "one is getting scammed, and that no one is getting unsolicited questions.\n\n*If you ever need to "
                    "speak with the mod team, tag the mods & let us know you need to talk. We will pull you into a "
                    "private channel.*"
                ),
                "labels": ("dm", "dming", "pm"),
            },
            "No Soliciting, Propositioning, or Promoting": {
                "description": (
                    "This isn’t a job board. This is not a place for promotions of your stuff. We do not allow the "
                    "exchange of money. We do not do work for people. **We’re here to help you understand the code "
                    "you’re writing, that is all.**\n\n*If you have something you think we'd like to promote talk to "
                    "the mods.*"
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
            "Keep It Legal": {
                "description": (
                    "No discussion is allowed of anything that breaks the law or violates the terms of service for a "
                    "product or service. You don’t need to do either to learn. This covers account creation bots, scam "
                    "bots, purchase automation bots, DDoS, RATs, etc."
                ),
                "labels": ("tos", "hacker", "illegal", "hack", "hacking"),
            },
            "Be Understanding, Respectful, & Helpful": {
                "description": (
                    "This community has members with an incredible diversity of opinions, experiences, and skill "
                    "levels. Be aware and understanding. Your opinions aren’t more important than anyone else’s. "
                    "*Strong opinions* are great, just *hold them weakly.* You’ll learn more and others will be more "
                    "willing to hear you out."
                ),
                "labels": (
                    "understanding",
                    "respectful",
                    "helpful",
                    "trolling",
                    "helping",
                    "learning",
                ),
            },
            "Academic Honesty": {
                "description": (
                    "We will help you understand your homework, we will help you figure out the solution, __we will "
                    "not give you the answers__. For tests and quizzes we can help you with your studying, we can only "
                    "give you vague nudges in the right direction on quizzes, __we will not help with tests__."
                ),
                "labels": (
                    "academics",
                    "honesty",
                    "homework",
                    "quizzes",
                    "tests",
                    "school",
                    "cheating",
                    "dishonest",
                ),
            },
            "Keep It Civil & Decent": {
                "description": (
                    "No *harassment, NSFW content, flaming, trolling,* or *bigotry* will be tolerated. This includes "
                    "derogatory remarks towards or statements objectifying anyone (on the server or not).\n\n__Trolling"
                    " people who are learning as well as unhelpful behavior in help channels will not be permitted.__"
                ),
                "labels": (
                    "nsfw",
                    "trolling",
                    "harassment",
                    "bigotry",
                    "harassing",
                    "racism",
                    "derogatory",
                    "objectification",
                ),
            },
            "Spam & Getting Help": {
                "description": (
                    "To help keep the server organized & avoid confusion, please keep coding questions out of "
                    "discussion channels. Do not spam multiple channels with your questions, do not direct people to "
                    "your help channel, and please abide by directions given by the server staff."
                ),
                "labels": ("help", "spam", "questions", "confusion"),
            },
            "Display Names & PFPs Should be Appropriate": {
                "description": (
                    "Your username should be readable, should not be promotional, and should not violate the previous "
                    "rule. Your PFP should be reasonably appropriate (no NSFW content, nothing objectionable, nothing "
                    "promotional)."
                ),
                "labels": ("nickname", "avatar", "name", "pfp", "username"),
            },
            "Use English Only": {
                "description": (
                    "To ensure everyone can participate and that the server staff can foster an environment amenable "
                    "to growth and learning, please only use __English__. If you cannot reasonably communicate in "
                    "English you may be removed from the server."
                ),
                "labels": ("english",),
            },
        }

    @Cog.command(name="update-rules")
    @commands.has_guild_permissions(manage_channels=True)
    async def update_rules_message(self, ctx, *, reason: str):
        rules: nextcord.TextChannel = nextcord.utils.get(
            self.server.channels, name="👮rules"
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
            timestamp=datetime.now().astimezone(pytz.timezone("US/Eastern")),
            color=BLUE,
        )
        embed.set_footer(text=admin.name, icon_url=admin.avatar.url)

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
