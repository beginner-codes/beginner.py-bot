from typing import Any, Union
import json
import pathlib


class RunnerConfig:
    def __init__(self, config_path: Union[str, pathlib.Path]):
        self._config_path = pathlib.Path(config_path)
        self._config_cache = {}

    def get(self, name: str) -> Any:
        if name not in self._config_cache:
            self._load(name)
        return self._config_cache[name]

    def reload(self, name: str) -> Any:
        self._load(name)
        return self.get(name)

    def _load(self, name: str):
        path = self._config_path / f"{name}.json"
        if not path.exists():
            raise FileNotFoundError(f"No such config file ({path.resolve()})")

        with open(path, "r") as json_file:
            self._config_cache[name] = json.load(json_file)
