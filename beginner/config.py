import beginner.logging
import functools
import os
import pathlib
import yaml
from typing import Any, Dict, Optional, Sequence, Protocol


class ScopedGetter:
    def __call__(self, name: str, *, env_name: Optional[str] = None, default: Any = None) -> Any:
        ...


@functools.lru_cache()
def get_config(filename: str) -> Dict[str, Any]:
    logger = beginner.logging.get_logger()

    project = pathlib.Path(__file__).parent.parent
    file_path = project / f"{filename}.yaml"

    logger.debug(f"Loading config file: {file_path.resolve()}")
    if not file_path.exists():
        return {}

    with open(file_path, "r") as yaml_file:
        return yaml.safe_load(yaml_file)


def scope_getter(scope: str, filenames: Optional[Sequence[str]] = None) -> ScopedGetter:
    def scoped(name: str, *, env_name: Optional[str] = None, default: Any = None) -> Any:
        kwargs = {}
        if filenames:
            kwargs["filenames"] = filenames
        return get_setting(
            name, scope=scope, env_name=env_name, default=default, **kwargs
        )

    return scoped


def get_setting(
    name: str,
    *,
    filenames: Sequence[str] = ("production", "development"),
    scope: str = "env",
    env_name: Optional[str] = None,
    default: Any = None,
) -> Any:
    """ Searches through yaml config files and the environment for a setting. """
    not_set = object()
    value = not_set
    for file in (get_config(filename) for filename in filenames):
        value = file.get(scope, {}).get(name, value)

    if value is not_set and (env_name is not None or scope == "env"):
        value = os.getenv(env_name if env_name else name, not_set)

    return default if value is not_set else value


def get_scope(
    scope: str,
    *,
    filenames: Sequence[str] = ("production", "development")
) -> Any:
    keys = set()
    for file in (get_config(filename) for filename in filenames):
        keys.update(file.get(scope, {}).keys())

    for key in keys:
        value = None
        for file in (get_config(filename) for filename in filenames):
            value = file.get(scope, {}).get(key, value)
        yield key, value
