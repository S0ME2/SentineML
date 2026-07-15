from app.application.ports.health import (
    DatabaseHealthCheck,
    RedisHealthCheck,
)


class CheckDatabaseHealth:
    def __init__(self, health_check: DatabaseHealthCheck):
        self._health_check = health_check

    def execute(self) -> bool:
        return self._health_check.is_healthy()


class CheckRedisHealth:
    def __init__(self, health_check: RedisHealthCheck):
        self._health_check = health_check

    def execute(self) -> bool:
        return self._health_check.is_healthy()
