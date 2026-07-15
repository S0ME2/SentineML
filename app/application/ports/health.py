from typing import Protocol


class DatabaseHealthCheck(Protocol):
    def is_healthy(self) -> bool: ...


class RedisHealthCheck(Protocol):
    def is_healthy(self) -> bool: ...
