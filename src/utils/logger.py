import functools
import logging
import sys
from datetime import datetime, timedelta, timezone

IS_DEBUG = True


def setup_logger():
    def logger_time(*args):
        """ロガーのタイムスタンプを生成する関数"""
        jst = timezone(timedelta(hours=9))
        return datetime.now(jst).timetuple()

    logger = logging.getLogger(__name__)
    logger.propagate = False
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter(
        "[%(levelname)s] %(asctime)s.%(msecs)03d %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    formatter.converter = logger_time

    # stdoutのログハンドラを追加
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger


logger = setup_logger()
if IS_DEBUG:
    logger.setLevel(logging.DEBUG)
else:
    logger.setLevel(logging.INFO)


def debug(func):
    """デバッグログを出力するデコレータ"""

    @functools.wraps(func)
    def wrapper_debug(*args, **kwargs):
        # 関数の引数を文字列化
        args_repr = [repr(a) for a in args]
        kwargs_repr = [f"{k}={v!r}" for k, v in kwargs.items()]
        signature = ", ".join(args_repr + kwargs_repr)

        # 関数呼び出しをログに記録
        logger.info(f"Calling {func.__name__}({signature})")

        # 関数を実行
        value = func(*args, **kwargs)

        # 戻り値をログに記録
        logger.info(f"{func.__name__!r} returned {value!r}")

        return value

    return wrapper_debug
