import asyncio
import threading
import time
from functools import wraps
from typing import Any, Callable, Coroutine, ParamSpec, TypeVar

P = ParamSpec("P")
R = TypeVar("R")


class RateLimit:
    def __init__(
        self,
        tokens_per_second: float = 1.0,
        capacity: float = 2,
    ):
        """
        A simple rate limiter that enforces a maximum number of calls per second.

        Args:
            tokens_per_second (float): Maximum number of allowed tokens per second.

        Usage:
            limiter = RateLimiter(tokens_per_second=3, max_tokens=10)

            @limiter
            def fetch(url): ...
        """
        self.tokens: float = 0
        self.capacity: float = capacity
        self.tokens_per_second: float = tokens_per_second

        if tokens_per_second > 0:
            self._interval = 1.0 / tokens_per_second
        else:
            self._interval = float("inf")

        self._last_checked = time.monotonic()

        self._lock = threading.Lock()

    def _acquire(self) -> float:
        """Return seconds the caller should wait before proceeding."""

        # Rate limiting disabled
        if self.tokens_per_second <= 0:
            return 0

        with self._lock:
            now = time.monotonic()
            elapsed = now - self._last_checked

            self.tokens += elapsed * self.tokens_per_second
            self.tokens = min(self.capacity, self.tokens)

            self._last_checked = now

            if self.tokens < 1:
                deficit = 1 - self.tokens
                self.tokens -= 1
                return deficit / self.tokens_per_second
            else:
                self.tokens -= 1
                return 0

    def aio_limit(
        self, func: Callable[P, Coroutine[Any, Any, R]]
    ) -> Callable[P, Coroutine[Any, Any, R]]:
        """Return an asyncio rate-limited wrapper around *func*."""

        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            delay = self._acquire()
            if delay > 0:
                await asyncio.sleep(delay)
            return await func(*args, **kwargs)

        return wrapper

    def limit(self, func: Callable[P, R]) -> Callable[P, R]:
        """Return a rate-limited wrapper around *func*."""

        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            delay = self._acquire()
            if delay > 0:
                time.sleep(delay)
            return func(*args, **kwargs)

        return wrapper

    # Allow using the instance itself as a decorator: @limiter
    def __call__(self, func: Callable[P, R]) -> Callable[P, R]:
        return self.limit(func)
