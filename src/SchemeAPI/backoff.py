import random
import time
from functools import wraps
from typing import Callable, ParamSpec, Type, TypeVar

P = ParamSpec("P")
R = TypeVar("R")


class RetryError(Exception):
    """Raised when all retry attempts for a function have failed."""


def backoff(
    exception_type: tuple[Type[Exception], ...] | Type[Exception] = Exception,
    max_attempts: int = 3,
    base_delay: float = 1,
):
    """
    Decorator that retries a function call using exponential backoff.

    The function is retried up to `max_attempts` times when it raises one of
    the specified exceptions. Between attempts, an exponential backoff delay
    (base_delay * 2^attempt) with jitter is applied.

    Raises:
        RetryError: if all retry attempts fail.
        Exception: the last exception is attached as context.
    """

    def decorator(func: Callable[P, R]) -> Callable[P, R]:

        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            last_exc: Exception | None = None

            for attempt in range(max_attempts):
                try:
                    result = func(*args, **kwargs)
                    return result

                except exception_type as e:
                    last_exc = e

                    print(
                        f"\n[RETRY] {func.__name__} "
                        f"(attempt {attempt + 1}/{max_attempts})\n"
                        f"  ↳ {type(e).__name__}: {e}\n"
                        f"  ↳ {func.__code__.co_filename}:{func.__code__.co_firstlineno}\n"
                    )
                    if attempt == max_attempts - 1:
                        break

                    delay = int(base_delay * (2**attempt))
                    jitter = random.uniform(0, 1)

                    print(
                        f"\rRetrying in {delay + round(jitter)}s...   ",
                        end="",
                        flush=True,
                    )
                    time.sleep(jitter)
                    for remaining in range(delay, 0, -1):
                        print(f"\rRetrying in {remaining}s...   ", end="", flush=True)
                        time.sleep(1)

                    print("\rRetrying now!            ")

            raise RetryError(
                f"{func.__name__} failed after {max_attempts} attempts"
            ) from last_exc

        return wrapper

    return decorator
