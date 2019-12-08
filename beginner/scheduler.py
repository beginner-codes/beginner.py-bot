from __future__ import annotations
from beginner.exceptions import BeginnerException
from beginner.models.scheduler import Scheduler as SchedulerTasks
from collections import defaultdict
from datetime import datetime
from functools import cached_property
from typing import Any, AnyStr, Callable, Union
import pickle


class Scheduler:
    """ System for scheduling actions and having them execute at a given date and time. """

    __task_handlers__ = defaultdict(list)

    def __init__(self):
        pass

    @cached_property
    def tasks(self):
        tasks = defaultdict(list)
        for task in SchedulerTasks.select():
            tasks[task.name].append(task)
        return tasks

    def schedule(
        self, name: AnyStr, when: datetime, tag: AnyStr, payload: Any = None
    ) -> Scheduler:
        self.tasks[name].append(
            Task(
                SchedulerTasks(
                    name=name, when=when, tag=tag, payload=pickle.dumps(payload)
                )
            )
        )

    @classmethod
    async def trigger_tag(cls, tag: AnyStr):
        if tag not in cls.__task_handlers__:
            raise TagNotRegistered(f"The tag '{tag}' has not been registered")


class Task:
    """ Wrapper around a scheduler task. """

    def __init__(self, task: SchedulerTasks):
        self._task = task

    @property
    def ID(self):
        return self.task.ID

    @property
    def name(self) -> AnyStr:
        return self.task.name

    @name.setter
    def name(self, value: AnyStr):
        self.task.name = value

    @property
    def payload(self) -> Any:
        return pickle.loads(self.task.payload)

    @payload.setter
    def payload(self, value: Any):
        self.task.payload = pickle.dumps(value)

    @property
    def tag(self) -> AnyStr:
        return self.task.tag

    @tag.setter
    def tag(self, value: AnyStr):
        self.task.tag = value

    @property
    def task(self) -> SchedulerTasks:
        return self._task

    @property
    def when(self) -> datetime:
        return self.task.when

    @when.setter
    def when(self, value: datetime):
        self.task.when = value

    def save(self):
        """ Handy helper to save changes made to the task to the database. """
        self.task.save()


def tag(callback: Union[AnyStr, Callable]) -> Callable:
    """ Decorator to tag a callback. """
    def save_tag(callback: Callable, tag: AnyStr = callback) -> Callable:
        """ Save a callback for a given tag. """
        Scheduler.__task_handlers__[tag].append(callback)
        return callback

    tag = callback
    if callable(callback):
        tag = callback.__name__
        return save_tag(callback, tag)
    return save_tag


class TagNotRegistered(BeginnerException):
    pass
