from peewee import *  # Make everything available here to simplify imports


class Model(Model):
    """ Base model for beginner.py models. """
    pass


def set_database(db: Database) -> None:
    """ Take a peewee database and bind it to all beginner.py models. """
    db.bind(Model.__subclasses__())
    return
