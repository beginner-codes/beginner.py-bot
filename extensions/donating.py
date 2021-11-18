from discord import Message
import dippy


class DonatingExtension(dippy.Extension):
    @dippy.Extension.command("!donate")
    async def manage_streaming_permissions(self, message: Message):
        await message.channel.send(
            (
                f"You can make donations to help support Beginner.Codes using Buy Me a Coffee! "
                f"https://www.buymeacoffee.com/beginnercodes"
            ),
            reference=message,
            delete_after=120,
        )
        await message.delete(delay=120)
