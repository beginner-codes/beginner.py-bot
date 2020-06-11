from __future__ import annotations
from beginner.logging import create_logger
from beginner.settings import Settings
from beginner.tags import TaggableMeta
from discord.ext import commands
from discord import TextChannel, Client, Guild, Emoji, CategoryChannel, Role
from typing import Any, AnyStr, Callable, Coroutine, List, Optional, Union
import json
import os.path


class Cog(commands.Cog, metaclass=TaggableMeta):
    def __init__(self, client: Client):
        self.settings = Settings()
        self.client = client
        self.logger = create_logger(self.__class__.__name__)

    @commands.Cog.listener()
    async def on_ready(self):
        self.logger.debug("Cog ready")

    @property
    def server(self) -> Guild:
        return self.client.get_guild(644299523686006834)

    def get_emoji(self, name: AnyStr, default: Optional[Any] = None) -> Emoji:
        return self.get(self.server.emojis, name, default)

    def get_category(
        self, name: AnyStr, default: Optional[Any] = None
    ) -> CategoryChannel:
        return self.get(self.server.categories, name, default, preserve_case=True)

    def get_channel(self, name: AnyStr, default: Optional[Any] = None) -> TextChannel:
        return self.get(self.server.channels, name, default)

    def get_role(self, name: AnyStr, default: Optional[Any] = None) -> Role:
        return self.get(self.server.roles, name, default, preserve_case=False)

    def get(
        self,
        search: List,
        name: AnyStr,
        default: Optional[Any] = None,
        preserve_case: bool = True,
    ):
        for element in search:
            ename = element.name if preserve_case else element.name.lower()
            if ename == name:
                return element
        return default

    @staticmethod
    def load_data(namespace: AnyStr, default: Any = None) -> Optional[Any]:
        data = None
        path = os.path.join("data", f"{namespace}.json")
        if os.path.exists(path):
            with open(path, "r") as json_file:
                try:
                    data = json.load(json_file)
                except json.decoder.JSONDecodeError:
                    pass
        return data if data else default

    @staticmethod
    def update_data(namespace: AnyStr, data: Any):
        path = os.path.join("data", f"{namespace}.json")
        with open(path, "w") as json_file:
            json.dump(data, json_file)

    @staticmethod
    def command(*args, **kwargs) -> Any:
        return commands.command(*args, **kwargs)


class AdvancedCommand:
    def __init__(self, default: Coroutine, fail: Optional[Coroutine] = None):
        self._default = default
        self._fail = fail
        self._options = {}

    def add(self, name: AnyStr, handler: Coroutine) -> AdvancedCommand:
        self._options[name.lower()] = handler
        return self

    async def run(self, ctx, *args):
        option = args[0].lower() if args else None
        handler = self._options.get(option, self._default)
        message = args
        if option and option in self._options:
            message = args[1:]
        elif self._fail:
            handler = self._fail
        await handler(ctx, *message)
