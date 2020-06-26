from beginner.runner.buffer import RunnerOutputBuffer
from beginner.runner.config import RunnerConfig
from beginner.runner.module_wrapper import ModuleWrapper, RunnerAttributeError
from typing import Any, Callable, Dict, Tuple, Union
import bevy


class RunnerBuiltinWrappers(bevy.Bevy):
    config: RunnerConfig
    buffer: RunnerOutputBuffer

    def get(self, name: str, default: Any = None) -> Union[Callable, Any]:
        if hasattr(self, name):
            return getattr(self, name)
        return default

    def buffer_printer(self, *args, **kwargs):
        kwargs["file"] = self.buffer
        return print(*args, **kwargs)

    def safe_getattr(self, obj: Any, name: str) -> Any:
        if name.startswith("__") and name not in self.config.get("enabled_special_attributes"):
            obj_name = obj.__name__ if hasattr(obj, "__name__") else obj.__class__.__name__
            raise RunnerAttributeError(f"The attribute or method '{obj_name}.{name}' is disabled for security reasons")

    def safe_import(
        self,
        name: str,
        globals_dict: Dict[str, Any] = {},
        locals_dict: Dict[str, Any] = {},
        from_list: Tuple = tuple(),
        level: int = 0,
    ) -> Union[ModuleWrapper, Tuple[Any]]:
        return ModuleWrapper.context(self.config).build(
            __import__(name, globals_dict, locals_dict, from_list, level)
        )
