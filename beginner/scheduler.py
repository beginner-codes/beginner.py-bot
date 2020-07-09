from __future__ import annotations
from beginner.exceptions import BeginnerException
from beginner.logging import get_logger
from beginner.models.scheduler import Scheduler
from beginner.tags import build_tag_set, fetch_tags
from datetime import datetime, timedelta
from typing import Any, AnyStr, Callable, Dict, Set, Union
import asyncio
import pickle


logger = get_logger(("beginner.py", "scheduler"))


def initialize_scheduler(loop=asyncio.get_event_loop()):
    """ Loads scheduler tasks from the database and schedules them to run. """
    for task in Scheduler.select():
        loop.create_task(_schedule(task, pickle.loads(task.payload.encode())))


def schedule(
    name: AnyStr,
    when: Union[datetime, timedelta],
    callback_tag: Union[AnyStr, Callable],
    *args,
    loop=asyncio.get_event_loop(),
    no_duplication=False,
    **kwargs,
):
    """ Schedule a task to be run and save it to the database. """
    if no_duplication and task_scheduled(name):
        return False

    tags = build_tag_set(callback_tag)  # Get tags into a set
    # We don't want the "schedule" tag which is required for all tasks
    if "schedule" in tags:
        tags.remove("schedule")
    when = datetime.now() + when if isinstance(when, timedelta) else when
    time = _seconds_until_run(when)
    payload = {"args": args, "kwargs": kwargs}
    if time <= 0:
        raise TaskScheduledForPast(
            f"Task {name} was scheduled for {when} which was {time} seconds ago ({datetime.now()})"
        )
    task = _schedule_save(name, when, tags, pickle.dumps(payload, 0).decode())
    loop.create_task(_schedule(task, payload))
    return True


def task_scheduled(name):
    return _count_scheduled(name) > 0


async def _schedule(task: Scheduler, payload: Dict):
    """ Schedules a task and calls the """
    time = _seconds_until_run(task.when)
    logger.debug(f"Scheduling {task.name} for {task.when}")
    if time > 0:
        await asyncio.sleep(time)
    logger.debug(f"Triggering {task.name} running callbacks tagged {task.tag}")
    logger.debug(f"- SCHEDULED FOR: {task.when}")
    logger.debug(f"- RUNNING AT:    {datetime.now()}")
    await _trigger_task(task, payload)


def _count_scheduled(name: AnyStr) -> int:
    return Scheduler.select().where(Scheduler.name == name).count()


def _schedule_save(
    name: AnyStr, when: datetime, tags: Set, payload: AnyStr
) -> Scheduler:
    """ Takes task parameters and creates a Scheduler row in the database. """
    tag = ",".join(map(str, tags))  # Convert the tag set to a string
    task = Scheduler(name=name, when=when, tag=tag, payload=payload)
    task.save()
    logger.debug(f"Saved {task.name} for {task.when}")
    return task


def _seconds_until_run(when: datetime) -> float:
    return (when - datetime.now()).total_seconds()


async def _trigger_task(task: Scheduler, payload: Any):
    """ Runs the callbacks tagged for this task and removes the task from the database. """
    tags = set(task.tag.split(","))
    name = task.name
    task.delete_instance()
    ran = await _run_tags(tags, payload)
    logger.debug(f"Attempted to run {ran} callback{'s' if ran > 1 else ''} for {name}")


async def _run_tags(tags: Set, payload: Dict):
    """ Runs all callbacks with the appropriate tags. """
    callbacks = fetch_tags("schedule", tags)
    try:
        for callback in callbacks:
            if asyncio.iscoroutine(callback) or asyncio.iscoroutinefunction(callback):
                await callback(*payload["args"], **payload["kwargs"])
            else:
                callback(*payload["args"], **payload["kwargs"])
    finally:
        return len(callbacks)


class TaskScheduledForPast(BeginnerException):
    pass


class TaskCallbackMissingSchedulerTag(BeginnerException):
    pass
