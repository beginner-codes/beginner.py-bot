import dippy
import discord


class PrivateChatExtension(dippy.Extension):
    @dippy.Extension.listener("message")
    async def on_message(self, message: discord.Message):
        if message.channel.id != 850187697397432361:
            return

        if message.author.bot:
            return

        if message.content[0] == "!":
            return

        await message.delete()
