import asyncio
import logging
import time
from collections import deque
from typing import Deque

__all__ = ["Throttler"]


class Throttler:
    def __init__(self, rate_limit: int, period=1.0):
        """
        An asynchronous rate limiter that throttles operations to stay within specified limits.

        Attributes:
            rate_limit (int): Maximum number of operations allowed within the period.
            period (float): Time window in seconds to enforce the rate limit.

        Credits:
            This implementation was adopted from:
            https://github.com/hallazzang/asyncio-throttle
        """
        self.rate_limit = rate_limit
        self.period = period

        self._logger = logging.getLogger()
        self._task_logs: Deque[float] = deque()

    def flush(self):
        """
        Remove expired timestamps from the internal tracking queue.
        """
        now = time.monotonic()
        while self._task_logs:
            if now - self._task_logs[0] > self.period:
                self._task_logs.popleft()
            else:
                break

    async def acquire(self):
        """
        Acquire permission to perform a rate-limited operation.

        This method will:
        1. Remove expired timestamps
        2. If below rate limit, allow immediate execution
        3. If at rate limit, wait precisely until a slot becomes available
        """
        # Clean up expired timestamps
        self.flush()

        # If we haven't reached the limit, proceed immediately
        if len(self._task_logs) < self.rate_limit:
            self._task_logs.append(time.monotonic())
            return

        # Calculate exactly when the oldest operation will expire
        oldest_timestamp = self._task_logs[0]
        wait_time = (oldest_timestamp + self.period) - time.monotonic()

        # Wait until a slot becomes available
        if wait_time > 0:
            self._logger.debug(f"Throttling XivApi request for {wait_time:.2f}s")
            await asyncio.sleep(wait_time)

        self._task_logs.popleft()
        self._task_logs.append(time.monotonic())

    async def __aenter__(self):
        await self.acquire()

    async def __aexit__(self, exc_type, exc, tb):
        pass
