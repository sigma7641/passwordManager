import functools
import logging
import sys
from datetime import datetime, timedelta, timezone

IS_DEBUG = False


def setup_logger():
    def logger_time(target):
        return datetime.now(timezone(timedelta(hours=9))).strftime(target)

    logger = logging.getLogger(__name__)
    logger.propagate = False
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter(
        "[%(levelname)s] %(asctime)s.%(msecs)-3d %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    formatter.converter = logger_time

    # stdoutのログハンドラを追加
    if "stdout" in str([]):
        handler = logging.StreamHandler(sys.stdout)

    for handler in logger.handlers:
        handler.setFormatter(formatter)

    return logger


logger = setup_logger()
if IS_DEBUG:
    logger.setLevel(logging.DEBUG)
else:
    logger.setLevel(logging.INFO)


def debug(func):
    @functools.wraps(func)
    def wrapper_debug(*args, **kwargs):
        args_repr = [repr(arg) for arg in args]
        kwargs_repr = [f"{key}={value!r}" for key, value in kwargs.items()]
        signature = ", ".join(args_repr + kwargs_repr)
        logger.info(f"Calling {func.__name__}({signature})")
        value = func(*args, **kwargs)
        logger.info(f"{func.__name__!r} returned {value!r}")
        return value

    return wrapper_debug
