from beginner.models.points import Points
from datetime import datetime
from typing import List, Tuple
import peewee


def give_user_kudos(kudos: int, user_id: int, giver_id: int, message_id: int):
    kudos = Points(
        awarded=datetime.utcnow(),
        user_id=user_id,
        giver_id=giver_id,
        message_id=message_id,
        points=kudos,
        point_type="KUDOS"
    )
    kudos.save()


def get_user_kudos(user_id) -> int:
    kudos = (
        Points.select(peewee.fn.SUM(Points.points))
        .where(Points.user_id == user_id, Points.point_type == "KUDOS")
        .scalar()
    )
    return 0 if kudos is None else kudos


def get_highest_kudos(num_users: int) -> List[Tuple[int, int]]:
    return (
        Points.select(Points.user_id, peewee.fn.SUM(Points.points))
        .limit(max(num_users, 1))
        .group_by(Points.user_id)
        .order_by(peewee.fn.SUM(Points.points).desc())
        .where(Points.point_type == "KUDOS")
        .tuples()
    )


def remove_kudos(message_id: int, giver_id: int):
    Points.delete().where(
        Points.message_id == message_id, Points.giver_id == giver_id, Points.point_type == "KUDOS"
    ).execute()


def get_kudos_given_since(giver_id: int, since: datetime):
    points = (
        Points.select(Points.awarded, Points.points)
        .where(Points.giver_id == giver_id, Points.point_type == "KUDOS", Points.awarded >= since)
        .order_by(Points.awarded.desc())
        .tuples()
    )
    return [(point[0], point[1]) for point in points]
