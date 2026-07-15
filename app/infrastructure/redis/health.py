from redis import Redis
from redis.exceptions import RedisError


class RedisClientHealthCheck:
    def __init__(self, client: Redis | None):
        self._client = client

    def is_healthy(self) -> bool:
        if self._client is None:
            return False

        try:
            return bool(self._client.ping())
        except RedisError:
            return False
