import discord
from beginner.cog import Cog
from googlesearch import search as google
from urllib.parse import quote_plus
from random import choice


class Google(Cog):
    def __init__(self, client):
        self.client = client
        self.colors = [0xEA4335, 0x4285F4, 0xFBBC05, 0x34A853]

    @Cog.listener()  # event decorator inside a cog
    async def on_ready(self):
        print("Google cog ready.")

    @Cog.command()  # command decorator inside a cog
    async def google(self, ctx, *, query):
        async with ctx.typing():
            color = choice(self.colors)
            url_search = (
                f"https://www.google.com/search?hl=en&q={quote_plus(query)}"
                "&btnG=Google+Search&tbs=0&safe=on"
            )
            message = await ctx.send(
                embed=self.create_google_message(
                    f"Searching...\n\n[More Results]({url_search})", color
                )
            )
            google_results = google(query, num=5, stop=5, safe="on")

        results = []
        for result in google_results:
            short = result[result.find("//") + 2 :].strip("/")
            if len(short) > 50:
                short = f"{short[:50]}..."
            results.append(f"{len(results) + 1}. [{short}]({result})\n")
            await message.edit(
                embed=self.create_google_message(
                    f"Results for \"{query}\"\n\n{''.join(results)}\n[More Results]({url_search})",
                    color,
                )
            )

    def create_google_message(self, message, color):
        return discord.Embed(description=message, color=color).set_author(
            name=f"Google Results", icon_url=self.server.icon_url
        )


def setup(client):
    client.add_cog(Google(client))
