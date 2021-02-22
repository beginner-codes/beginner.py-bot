from beginner.runner.config import RunnerConfig
from typing import Any
from types import ModuleType
import bevy


class ModuleWrapper(bevy.Bevy):
    config: RunnerConfig

    def __init__(self, module: ModuleType):
        self.__protected_module__ = (
            module  # Use dunder name so that our getattr code will protect it
        )
        self.__enabled_attributes = self.config.get("enabled_modules").get(
            self.__protected_module__.__name__, []
        )

        if not self.__enabled_attributes:
            raise RunnerImportError(
                f"The module '{self.__protected_module__.__name__}' is disabled for security reasons"
            )

    def __getattr__(self, name: str) -> Any:
        if name.startswith(f"_{self.__class__.__name__}__") or name.startswith("__"):
            return super().__getattribute__(name)

        attr = getattr(self.__protected_module__, name)
        if not self.__enabled_attribute(name):
            raise RunnerAttributeError(
                f"The attribute or method '{self.__protected_module__.__name__}.{name}' is disabled for security reasons"
            )

        if isinstance(attr, ModuleType):
            return ModuleWrapper.context(self.config).build(attr)

        return attr

    def __setattr__(self, name: str, value: Any):
        if (
            not hasattr(self, "__protected_module__")
            or name.startswith(f"_{self.__class__.__name__}__")
            or name.startswith("__")
        ):
            super().__setattr__(name, value)
            return

        if not self.__enabled_attribute(name):
            raise RunnerAttributeError(
                f"The attribute or method '{self.__protected_module__.__name__}.{name}' is disabled for security reasons"
            )

        setattr(self.__protected_module__, name, value)

    def __enabled_attribute(self, name: str) -> bool:
        return "*" in self.__enabled_attributes or name in self.__enabled_attributes


class RunnerImportError(ImportError):
    ...


class RunnerAttributeError(AttributeError):
    ...
