from typing import Any, Dict, Callable, Optional
from beginner.runner.config import RunnerConfig
from beginner.runner.builtin_wrappers import RunnerBuiltinWrappers
import bevy


class RunnerBuiltins(bevy.Bevy, dict):
    config: RunnerConfig
    wrappers: RunnerBuiltinWrappers

    def __init__(self):
        self.__enabled_builtins = self.config.get("enabled_builtins")

    def get_builtins(self) -> Dict[str, Any]:
        builtins = {}
        for name, value in __builtins__.items():
            if name in self.__enabled_builtins:
                builtins[name] = self.wrappers.get(self.__enabled_builtins[name], value)
        return builtins
