from beginner.models.kudos import Kudos
from datetime import datetime
from typing import List, Tuple
import peewee


def give_user_kudos(kudos: int, user_id: int, giver_id: int, message_id: int):
    kudos = Kudos(
        given=datetime.utcnow(),
        user_id=user_id,
        giver_id=giver_id,
        message_id=message_id,
        kudos=kudos,
    )
    kudos.save()


def get_user_kudos(user_id) -> int:
    kudos = (
        Kudos.select(peewee.fn.SUM(Kudos.kudos))
        .where(Kudos.user_id == user_id)
        .scalar()
    )
    return 0 if kudos is None else kudos


def get_highest_kudos(num_users: int) -> List[Tuple[int, int]]:
    return (
        Kudos.select(Kudos.user_id, peewee.fn.SUM(Kudos.kudos))
        .limit(max(num_users, 1))
        .group_by(Kudos.user_id)
        .order_by(peewee.fn.SUM(Kudos.kudos).desc())
        .tuples()
    )


def remove_kudos(message_id: int, giver_id: int):
    Kudos.delete().where(
        Kudos.message_id == message_id, Kudos.giver_id == giver_id
    ).execute()


def get_last_kudos_given(giver_id, user_id):
    row = (
        Kudos.select(Kudos.given)
        .where(Kudos.user_id == user_id, Kudos.giver_id == giver_id)
        .order_by(Kudos.given.desc())
        .tuples()
        .get_or_none()
    )
    return row[0] if row else None
