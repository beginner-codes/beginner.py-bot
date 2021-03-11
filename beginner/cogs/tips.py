from beginner.cog import Cog
from beginner.models.messages import Message, MessageTypes
from discord import Embed


class TipsCog(Cog):
    @Cog.command()
    async def tip(self, ctx, *, unsanitized_label=None):
        label = self.sanitize_label(unsanitized_label)
        tip = self.get_tip(label) if label else None
        if not label:
            await self.list_tips(ctx.message.channel, self.get_tips())
        elif tip:
            await self.show_tip(tip, ctx.message.channel)
        else:
            tips = self.get_tips(label)
            if len(tips) == 1:
                await self.show_tip(tips[0], ctx.message.channel)
            else:
                await self.list_tips(ctx.message.channel, tips, label)

    @Cog.command()
    async def tip_details(self, ctx, *, unsanitized_label):
        label = self.sanitize_label(unsanitized_label)
        tip = self.get_tip(label)
        if not tip:
            await ctx.send(f"No tip matched {label!r}")
            return

        content = "\n".join(f"> {section}" for section in tip.message.split("\n"))
        await ctx.send(
            f"Title: {tip.title!r}\n"
            f"Labels: {tip.label!r}\n"
            f"Content:\n{content}\n"
            f"Author: {tip.author}"
        )

    @Cog.command(name="delete-tip")
    async def delete_tip(self, ctx, *, unsanitized_label=None):
        label = self.sanitize_label(unsanitized_label)
        tips = self.get_tips(label)
        if not tips:
            await ctx.send(f"No tip matches `{label}`")
        else:
            for tip in tips:
                tip.delete_instance()
                await ctx.send(f"Deleting tip `{tip.title} - {tip.label}`")

    @Cog.command(name="create-tip")
    async def create_tip(self, ctx, *, unsanitized_label):
        label = self.sanitize_label(unsanitized_label)
        if (
            not ctx.author.guild_permissions.manage_messages
            and self.get_role("helpers") not in ctx.author.roles
        ):
            return

        if not ctx.message.reference:
            await ctx.send(
                "You must reply to the message that you would like to make into a tip."
            )
            return

        if not label:
            await ctx.send(
                "You must provide a label that can be used to lookup the tip."
            )
            return

        tip = self.get_tip(label)
        message = await ctx.message.channel.fetch_message(
            ctx.message.reference.message_id
        )
        await ctx.send(
            'What would you like the title to be? Say "empty" if you\'d like to not have a title or "keep" if you\'re '
            "editing an existing tip and don't want to change the title."
        )
        title_message = await self.client.wait_for(
            "message",
            check=lambda msg: msg.channel == ctx.message.channel
            and msg.author == ctx.author,
        )
        title = (
            ""
            if title_message.clean_content == "empty"
            else title_message.clean_content
        )
        response = f'Created tip labeled "{label}"'
        if tip:
            await ctx.send(
                'Found an existing tip with that label, what would you like the label to be changed to? Say "keep" if '
                "you don't want it changed."
            )
            label_message = await self.client.wait_for(
                "message",
                check=lambda msg: msg.channel == ctx.message.channel
                and msg.author == ctx.author,
            )
            if label_message.clean_content.lower() != "keep":
                tip.label = self.sanitize_label(label_message.clean_content)
            tip.message = message.content
            tip.author = message.author.display_name
            if title != "keep":
                tip.title = title
            response = f'Updated tip labeled "{label}"'
        else:
            tip = Message(
                label=label,
                message=message.content,
                message_type=MessageTypes.TIP.name,
                author=message.author.display_name,
                title=title,
            )
        tip.save()
        await ctx.send(
            embed=Embed(
                description=f"Title:\n{tip.title if tip.title else '*NO TITLE*'}\n\nMessage:\n{tip.message}",
                color=0x306998,
            ).set_author(name=response, icon_url=self.server.icon_url)
        )

    async def list_tips(self, channel, tips, label=None):
        formatted = [f"- {tip.label}" for tip in tips]
        message = "Here are all tips that are available"
        title = "Available Tips"

        if label:
            message = f"Here are the tips that are similar to *{label}*"
            title = "Possible Matches"

        if not len(formatted):
            message = "*No Tips Found*"

        embed = Embed(description=message, color=0x306998, title=title)
        while formatted:
            index = min(len(formatted), 5)
            embed.add_field(name="- - - -", value="\n".join(formatted[:index]))
            formatted = formatted[index:]

        await channel.send(embed=embed)

    async def show_tip(self, tip, channel):
        title = tip.title if tip.title else Embed.Empty
        embed = Embed(description=tip.message, title=title, color=0x306998).set_footer(
            text=f"Contributed graciously by {tip.author}"
        )
        await channel.send(embed=embed)

    @staticmethod
    def get_tips(label=None):
        where = Message.message_type == MessageTypes.TIP.name
        if label:
            where = where & (Message.label.contains(f"%{label}%"))
        return Message.select().where(where).order_by(Message.label.asc()).execute()

    @staticmethod
    def get_tip(label):
        return Message.get_or_none(
            (Message.message_type == MessageTypes.TIP.name) & (Message.label == label)
        )

    @staticmethod
    def sanitize_label(label: str):
        return (
            label.casefold().translate({ord("-"): " ", ord("_"): " "})
            if label
            else label
        )


def setup(client):
    client.add_cog(TipsCog(client))
