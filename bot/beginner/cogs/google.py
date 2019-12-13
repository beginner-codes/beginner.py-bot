import discord
from beginner.cog import Cog
from bs4 import BeautifulSoup
import requests
import urllib
from random import randint


class Google(Cog):
    def __init__(self, client):
        self.client = client
        self.colors = [0xEA4335, 0x4285F4, 0xFBBC05, 0x34A853]

    @Cog.listener()  # event decorator inside a cog
    async def on_ready(self):
        print("Google cog ready.")

    @Cog.command()  # command decorator inside a cog
    async def google(self, ctx, *, query):
        results = []
        queryplus = urllib.parse.quote_plus(query)
        url = f"https://www.google.com/search?q={queryplus}"
        async with ctx.typing():
            re = requests.get(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.97 Safari/537.36"
                },
            )
            soup = BeautifulSoup(re.content, "html.parser")
            res = soup.find("div", {"id": "search"})

            rs = res.find_all("div", "r")
            counter = 0
            for r in rs:
                title = r.find("span", "S3Uucc")
                if title:
                    link = r.find("a")["href"]
                    if title.text and link:
                        results.append(f"[{title.text}]({link})")
                        counter += 1
                if counter > 2:
                    break

            description = "\n".join(results) if results else "*No Results Found*"
            embedded = discord.Embed(
                description=f'Results for *"{query}"*\n\n{description}\n\n[See more results]({url})',
                color=self.colors[randint(0, 3)],
            )
            embedded.set_author(
                name=f"Google Results",
                icon_url="https://cdn.discordapp.com/icons/644299523686006834/e69f6d4231a6e58eed5884625c4b4931.png",
            )
        await ctx.send(embed=embedded)


def setup(client):
    client.add_cog(Google(client))
