from logging import *


def create_logger(name=None):
    logger_path_name = ".".join(["beginnerpy"] + ([name.lower()] if name else []))
    logger = getLogger(logger_path_name)
    logger.name = name.upper() if name else "BEGINNER.PY"
    return logger
