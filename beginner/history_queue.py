from datetime import datetime, timedelta


class HistoryQueue:
    def __init__(self, max_age: timedelta):
        self._max_age = max_age
        self._history = []

    def __iter__(self):
        self._prune()
        return iter(self._history)

    def add(self, *values):
        self._prune()
        self._history.insert(0, (datetime.utcnow(), *values))

    def _is_dirty(self) -> bool:
        if not self._history:
            return False

        return self._history[-1][0] < datetime.utcnow() - self._max_age

    def _prune(self):
        if not self._is_dirty():
            return

        oldest = datetime.utcnow() - self._max_age
        for index, (created, *_) in enumerate(self._history):
            if created < oldest:
                del self._history[index:]
                return
