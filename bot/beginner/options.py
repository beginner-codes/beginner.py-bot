from beginner.models.options import Option
from typing import Any, Optional
import pickle


def get_option(name: str, default: Optional[Any] = None) -> Any:
    option = Option.get_or_none(name=name)
    if not option or not option.value:
        return default
    return pickle.loads(option.value.encode())


def set_option(name: str, value: Any):
    dump = pickle.dumps(value, 0).decode()
    option = Option.get_or_none(name=name)
    if option:
        option.value = dump
    else:
        option = Option(name=name, value=dump)
    option.save()
