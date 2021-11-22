import typing as ty
import time

DEFAULT_MAX_ATTEMPTS = 10
DEFAULT_WAITING_TIME = 1  # seconds
DEFAULT_EXCEPTION = Exception


def retry_func(
    f: ty.Callable,
    *args,
    max_attempts: int = DEFAULT_MAX_ATTEMPTS,
    waiting_time: float = DEFAULT_WAITING_TIME,
    only_exception_type=DEFAULT_EXCEPTION,
    **kwargs,
) -> ty.Tuple[ty.Any, int]:
    """Wrapper that, when applied, retries running the function

    Args:
        f: function
        max_attempts: max attempts
        waiting_time: time in seconds between attempts
        only_exception_type: if specified, we only retry for this exception

    Returns: the result of the function and the number of times it was called
    """

    result = None
    times_called = 0
    while times_called < max_attempts:
        try:
            times_called += 1
            result = f(*args, **kwargs)
            return result, times_called
        except only_exception_type as e:
            if times_called >= max_attempts:
                raise e
            time.sleep(waiting_time)
    return result, times_called