from discord.ext import commands
from typing import Any, AnyStr, Union
import json
import os.path


class Cog(commands.Cog):
    @staticmethod
    def command(*args, **kwargs):
        return commands.command(*args, **kwargs)

    @staticmethod
    def load_data(namespace: AnyStr) -> Union[Any, None]:
        path = os.path.join("data", f"{namespace}.json")
        if os.path.exists(path):
            with open(path, "r") as json_file:
                return json.load(json_file)
        return None
