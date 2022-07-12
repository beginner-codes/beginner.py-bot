from beginner.models.settings import Settings as SettingsModel
from typing import Any, AnyStr, Optional
import pickle


class NOT_SET_TYPE:
    def __init__(self, name="NOT_SET"):
        self.name = name

    def __bool__(self):
        return False

    def __eq__(self, other):
        return False

    def __repr__(self):
        return f"<{self.name} at 0x{id(self)}>"


class Settings:
    NOT_SET = NOT_SET_TYPE()
    ERROR = NOT_SET_TYPE("ERROR")

    def _get(self, name: AnyStr) -> Any:
        result = SettingsModel.select(SettingsModel.value).where(
            SettingsModel.name == name
        )
        value = Settings.NOT_SET
        if result.count():
            try:
                value = pickle.loads(result.scalar().encode())
            except pickle.UnpicklingError:
                return Settings.ERROR

        return value

    def _set(self, name: AnyStr, value: Any):
        pickled = pickle.dumps(value, 0)
        if self._get(name) is Settings.NOT_SET:
            SettingsModel(name=name, value=pickled).save()
        else:
            SettingsModel.update(value=pickled).where(
                SettingsModel.name == name
            ).execute()

    def all(self):
        return {
            row.name: self._load_pickle(row.value)
            for row in SettingsModel.select().distinct()
        }

    def _load_pickle(self, data):
        try:
            return pickle.loads(data.encode())
        except pickle.UnpicklingError:
            return "FAILED TO UNPICKLE"

    def get(self, name: AnyStr, default: Optional[Any] = None) -> Any:
        return default if (value := self._get(name)) is Settings.NOT_SET else value

    def __getitem__(self, item: AnyStr) -> Any:
        return self._get(item)

    def __setitem__(self, key: AnyStr, value: Any):
        self._set(key, value)
