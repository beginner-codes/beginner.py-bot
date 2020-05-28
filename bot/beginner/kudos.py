from beginner.models.points import Points
from datetime import datetime
from typing import List, Tuple
import peewee


def give_user_kudos(kudos: int, user_id: int, giver_id: int, message_id: int):
    kudos = Points(
        given=datetime.utcnow(),
        user_id=user_id,
        giver_id=giver_id,
        message_id=message_id,
        kudos=kudos,
    )
    kudos.save()


def get_user_kudos(user_id) -> int:
    kudos = (
        Points.select(peewee.fn.SUM(Points.kudos))
        .where(Points.user_id == user_id)
        .scalar()
    )
    return 0 if kudos is None else kudos


def get_highest_kudos(num_users: int) -> List[Tuple[int, int]]:
    return (
        Points.select(Points.user_id, peewee.fn.SUM(Points.kudos))
        .limit(max(num_users, 1))
        .group_by(Points.user_id)
        .order_by(peewee.fn.SUM(Points.kudos).desc())
        .tuples()
    )


def remove_kudos(message_id: int, giver_id: int):
    Points.delete().where(
        Points.message_id == message_id, Points.giver_id == giver_id
    ).execute()


def get_last_kudos_given(giver_id, user_id):
    row = (
        Points.select(Points.given)
        .where(Points.user_id == user_id, Points.giver_id == giver_id)
        .order_by(Points.given.desc())
        .tuples()
        .get_or_none()
    )
    return row[0] if row else None
