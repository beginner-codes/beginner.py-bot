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
                    results.append({"title": title.text, "link": link})
                    counter += 1
                if counter > 2:
                    break

            embedded = discord.Embed(
                description=f"*{query}*\n\n[{results[0]['title']}]({results[0]['link']})\n[{results[1]['title']}]({results[1]['link']})\n[{results[2]['title']}]({results[2]['link']})\nIf you don't like these sites, you can check the other results here:\n[Google search for {query}]({url})",
                color=self.colors[randint(0, 3)],
            )
            embedded.set_author(
                name="Here are 3 Google results for",
                icon_url="https://cdn.discordapp.com/icons/644299523686006834/e69f6d4231a6e58eed5884625c4b4931.png",
            )
            await ctx.send(embed=embedded)


def setup(client):
    client.add_cog(Google(client))
