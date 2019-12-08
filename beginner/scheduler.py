from __future__ import annotations
from beginner.exceptions import BeginnerException
from beginner.models.scheduler import Scheduler
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, AnyStr, Callable, Dict, List, Union
import asyncio
import math
import pickle


__tagged_handlers__ = defaultdict(list)


def initialize_scheduler():
    """ Loads scheduler tasks from the database and schedules them to run. """
    for task in Scheduler.select():
        asyncio.create_task(_schedule(task, pickle.loads(task.payload.encode())))


def schedule(
    name: AnyStr,
    when: Union[datetime, timedelta],
    callback_tag: Union[AnyStr, Callable],
    *args,
    **kwargs,
):
    """ Schedule a task to be run and save it to the database. """
    tag = callback_tag.tag if callable(callback_tag) else callback_tag
    when = datetime.now() + when if isinstance(when, timedelta) else when
    time = _seconds_until_run(when)
    payload = {"args": args, "kwargs": kwargs}
    if time <= 0:
        raise TaskScheduledForPast(
            f"Task {name} was scheduled for {when} which was {time} seconds ago"
        )
    task = _schedule_save(name, when, tag, pickle.dumps(payload, 0).decode())
    asyncio.get_event_loop().create_task(_schedule(task, payload))


async def _schedule(task: Scheduler, payload: Dict):
    """ Schedules a task and calls the """
    time = _seconds_until_run(task.when)
    print(f"SCHEDULER: Scheduling {task.name} for {task.when}")
    if time > 0:
        await asyncio.sleep(time)
    print(f"SCHEDULER: Triggering {task.name} running callbacks tagged {task.tag}")
    await _trigger_task(task, payload)


def _schedule_save(
    name: AnyStr, when: datetime, tag: AnyStr, payload: AnyStr
) -> Scheduler:
    """ Takes task parameters and creates a Scheduler row in the database. """
    task = Scheduler(name=name, when=when, tag=tag, payload=payload)
    task.save()
    print(f"SCHEDULER: Saved {task.name} for {task.when}")
    return task


def _seconds_until_run(when: datetime) -> int:
    return math.floor((when - datetime.now()).total_seconds())


async def _trigger_task(task: Scheduler, payload: Any):
    """ Runs the callbacks tagged for this task and removes the task from the database. """
    try:
        await _run_tags(task.tag, payload)
    finally:
        task.delete_instance()


async def _run_tags(tag: AnyStr, payload: Dict):
    """ Runs all callbacks for a given tag. """
    for callback in __tagged_handlers__[tag]:
        if asyncio.iscoroutine(callback) or asyncio.iscoroutinefunction(callback):
            await callback(*payload["args"], **payload["kwargs"])
        else:
            callback(*payload["args"], **payload["kwargs"])


def tag(callback: Union[AnyStr, Callable]) -> Callable:
    """ Decorator to tag a callback. """

    def save_tag(callback: Callable, tag: AnyStr = callback) -> Callable:
        """ Save a callback for a given tag. """
        __tagged_handlers__[tag].append(callback)
        callback.tag = tag
        return callback

    tag = callback
    if callable(callback):
        tag = callback.__name__
        return save_tag(callback, tag)
    return save_tag


class TaskScheduledForPast(BeginnerException):
    pass
