from discord.ext import commands
from typing import Any, AnyStr, Union
import json
import os.path


class Cog(commands.Cog):
    @staticmethod
    def load_data(namespace: AnyStr, default: Any=None) -> Union[Any, None]:
        data = None
        path = os.path.join("data", f"{namespace}.json")
        if os.path.exists(path):
            with open(path, "r") as json_file:
                data = json.load(json_file)
        return data if data else default

    @staticmethod
    def update_data(namespace: AnyStr, data: Any):
        path = os.path.join("data", f"{namespace}.json")
        with open(path, "w") as json_file:
            json.dump(data, json_file)

    @staticmethod
    def command(*args, **kwargs) -> Any:
        return commands.command(*args, **kwargs)
