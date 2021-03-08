from __future__ import annotations
from beginner.cog import Cog
from beginner.config import scope_getter
from discord.ext.commands import Context
import re
import requests
import urllib.parse


class WeatherPromptCog(Cog):
    def __init__(self, client):
        super().__init__(client)
        self.location_cache = {}
        self.config = scope_getter("prompts")

    @Cog.command()
    async def weather(self, ctx: Context, *, location: str):
        address, (lat, lng) = self.locate(location)
        if lat is None or lng is None:
            await ctx.send(f"Unable to locate the address: *{location}*")
            return

        current, feels = self.get_weather(lat, lng)
        await ctx.send(
            f"In {address} it's currently {current}° Fahrenheit, it feels like {feels}°."
        )

    @weather.error
    async def weather_error(self, ctx, error):
        await ctx.send(f"Whoooops, there was an error getting the weather\n{error}")

    def locate(self, location: str) -> tuple[str, tuple[float, float]]:
        clean_address = self.quote_location(location)
        if clean_address in self.location_cache:
            return self.location_cache[clean_address]

        data = requests.get(
            f"https://maps.googleapis.com/maps/api/geocode/json?"
            f"address={clean_address}&"
            f"key={self.maps_api_key()}"
        ).json()

        address = self.build_address(
            data.get("results", [{}])[0].get("address_components", [])
        )
        location_data = (
            data.get("results", [{}])[0].get("geometry", {}).get("location", {})
        )
        coords = location_data.get("lat", None), location_data.get("lng", None)
        self.location_cache[clean_address] = address, coords
        return address, coords

    def get_weather(self, lat: float, lng: float) -> tuple[float, float]:
        data = requests.get(
            f"https://api.openweathermap.org/data/2.5/weather?"
            f"lat={lat}&"
            f"lon={lng}&"
            f"appid={self.weather_api_key()}&"
            f"units=imperial"
        ).json()
        current = data.get("main", {})
        return current.get("temp", None), current.get("feels_like", None)

    def quote_location(self, location: str) -> str:
        return urllib.parse.quote_plus(re.sub(r"[^\d\w]+", " ", location.casefold()))

    def build_address(self, parts):
        address = []
        for part in parts:
            if "locality" in part["types"] and not address:
                address.append(part["long_name"])
            elif "administrative_area_level_1" in part["types"]:
                address.append(part["short_name"])
                break
            elif "country" in part["types"]:
                address.append(part["short_name"])
                break
        return " ".join(address)

    def maps_api_key(self):
        return self.config("maps_api_key", env_name="GOOGLE_MAPS_API_KEY")

    def weather_api_key(self):
        return self.config("weather_api_key", env_name="WEATHER_API_KEY")


def setup(client):
    client.add_cog(WeatherPromptCog(client))
