from discord.ext import commands
from typing import Any, AnyStr, Callable, Coroutine, NoReturn, Union
import json
import os.path


class Cog(commands.Cog):
    @staticmethod
    def load_data(namespace: AnyStr, default: Any=None) -> Union[Any, None]:
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
    def __init__(self, default: Coroutine, fail: Union[Coroutine, None]=None):
        self._default = default
        self._fail = fail
        self._options = {}

    def add(self, name: AnyStr, handler: Coroutine) -> "AdvancedCommand":
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
