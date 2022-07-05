from beginner.models.settings import Settings as SettingsModel
from typing import Any, AnyStr, Optional
import pickle


class NOT_SET:
    def __repr__(self):
        return f"<{self.__class__.__name__} at 0x{id(self)}>"


class Settings:
    NOT_SET = NOT_SET()

    def _get(self, name: AnyStr) -> Any:
        result = SettingsModel.select(SettingsModel.value).where(
            SettingsModel.name == name
        )
        value = Settings.NOT_SET
        if result.count():
            try:
                value = pickle.loads(result.scalar().decode())
            except pickle.UnpicklingError:
                SettingsModel.delete().where(SettingsModel.name == name)

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
            row.name: pickle.loads(row.value.encode())
            for row in SettingsModel.select().distinct()
        }

    def get(self, name: AnyStr, default: Optional[Any] = None) -> Any:
        return default if (value := self._get(name)) is Settings.NOT_SET else value

    def __getitem__(self, item: AnyStr) -> Any:
        return self._get(item)

    def __setitem__(self, key: AnyStr, value: Any):
        self._set(key, value)
