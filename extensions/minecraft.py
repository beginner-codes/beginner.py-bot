from datetime import datetime
import asyncio
import dippy
import dippy.labels
import discord


class MinecraftExtension(dippy.Extension):
    client: dippy.Client
    log: dippy.logging.Logging
    labels: dippy.labels.storage.StorageInterface

    @dippy.Extension.command("!minecraft")
    async def minecraft_command(self, message: discord.Message):
        if message.channel.id != 834200603474657321:
            return

        await message.channel.send(
            f"**Server Details**\n```\nJava Edition: mc.beginnerpy.com\nBedrock: mc.beginnerpy.com:8152\n```\n**Rules**"
            f"\n- Mods that give unfair advantage are not allowed.\n- If your mods or custom client get you banned you "
            f"may not be allowed back.\n- Griefing and such are not allowed."
        )
