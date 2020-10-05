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

    @Cog.command(name="create-tip")
    async def create_tip(self, ctx, message_id, *, unsanitized_label):
        label = self.sanitize_label(unsanitized_label)
        if not ctx.author.guild_permissions.manage_guild:
            return

        tip = self.get_tip(label)
        message = await ctx.message.channel.fetch_message(int(message_id))
        await ctx.send(
            'What would you like the title to be? Say "empty" if you\'d like to not have a title or "keep" if you\'re '
            "editing an existing tip."
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
                'What would you like the label to be? Say "keep" if you don\'t want it changed.'
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

        embed = Embed(description=message, color=0x306998)
        embed.set_author(name=title, icon_url=self.server.icon_url)
        while formatted:
            index = min(len(formatted), 5)
            embed.add_field(name="- - - -", value="\n".join(formatted[:index]))
            formatted = formatted[index:]

        await channel.send(embed=embed)

    async def show_tip(self, tip, channel):
        embed = Embed(description=tip.message, color=0x306998).set_footer(
            text=f"Contributed graciously by {tip.author}"
        )
        if tip.title:
            embed.set_author(name=tip.title, icon_url=self.server.icon_url)
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
            label.lower().translate({ord("-"): " ", ord("_"): " "}) if label else label
        )


def setup(client):
    client.add_cog(TipsCog(client))
