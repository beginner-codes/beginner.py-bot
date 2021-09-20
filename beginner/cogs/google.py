from beginner.cog import Cog
from googleapiclient.discovery import build as google
from urllib.parse import quote_plus
from random import choice
import beginner.config
import nextcord


class MoreResultsButton(nextcord.ui.View):
    def __init__(self, url_search):
        super().__init__()
        self.add_item(nextcord.ui.Button(label='Click Here', url=url_search))

        
class Google(Cog):
    def __init__(self, client):
        super().__init__(client)
        self.colors = [0xEA4335, 0x4285F4, 0xFBBC05, 0x34A853]

    @Cog.command()  # command decorator inside a cog
    async def google(self, ctx, *, query):
        google_settings = beginner.config.scope_getter("google")
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
            query_obj = google(
                "customsearch",
                "v1",
                developerKey=google_settings(
                    "custom_search_key", env_name="GOOGLE_CUSTOM_SEARCH_KEY"
                ),
            )
            query_result = (
                query_obj.cse()
                .list(
                    q=query,
                    cx=google_settings(
                        "custom_search_engine", env_name="GOOGLE_CUSTOM_SEARCH_ENGINE"
                    ),
                    num=5,
                )
                .execute()
            )

        results = []
        for result in query_result.get("items", []):
            title = result["title"]
            if len(title) > 77:
                title = f"{title[:77]}..."
            results.append(f"{len(results) + 1}. [{title}]({result['link']})\n")
        await message.edit(
            embed=self.create_google_message(
                f"Results for \"{query}\"\n\n{''.join(results)}",
                color,
            )
            ,view=MoreResultsButton(url_search)
        )

    def create_google_message(self, message, color):
        return nextcord.Embed(description=message, color=color).set_author(
            name=f"Google Results", icon_url=self.server.icon.url
        )


def setup(client):
    client.add_cog(Google(client))
