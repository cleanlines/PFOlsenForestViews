
import functools
import time
from BaseLogger import BaseLogger

class Decorator(object):

    logger = BaseLogger()

    def decorator(func):
        @functools.wraps(func)
        def wrapper_decorator(*args, **kwargs):
            # Do something before
            value = func(*args, **kwargs)
            # Do something after
            return value

        return wrapper_decorator

    @classmethod
    def timer(cls, func):
        """Print the runtime of the decorated function"""
        @functools.wraps(func)
        def wrapper_timer(*args, **kwargs):
            print(f"starting {func}")
            start_time = time.perf_counter()  # 1
            value = func(*args, **kwargs)
            end_time = time.perf_counter()  # 2
            run_time = end_time - start_time  # 3
            a_string = f"Finished {func.__name__!r} in {run_time:.4f} secs"
            print(a_string)
            cls.logger.log(a_string)
            return value

        return wrapper_timer
