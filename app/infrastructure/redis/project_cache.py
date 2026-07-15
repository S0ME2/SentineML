import json
import logging

from redis import Redis
from redis.exceptions import RedisError

from app.application.ports.caches import ProjectCache
from app.domain.projects import Project

logger = logging.getLogger(__name__)


class NullProjectCache:
    def get(self, project_id: int) -> Project | None:
        return None

    def put(self, project: Project) -> None:
        return None

    def invalidate(self, project_id: int) -> None:
        return None


class RedisProjectCache:
    def __init__(
        self,
        client: Redis,
        *,
        ttl_seconds: int,
        key_prefix: str = "sentinelml:project",
    ):
        self._client = client
        self._ttl_seconds = ttl_seconds
        self._key_prefix = key_prefix

    def _key(self, project_id: int) -> str:
        return f"{self._key_prefix}:{project_id}"

    def get(self, project_id: int) -> Project | None:
        raw_value = self._client.get(self._key(project_id))
        if raw_value is None:
            return None

        data = json.loads(raw_value)
        return Project(
            id=data["id"],
            name=data["name"],
            description=data.get("description"),
        )

    def put(self, project: Project) -> None:
        if project.id is None:
            raise ValueError("Cannot cache a project without an id")

        payload = json.dumps(
            {
                "id": project.id,
                "name": project.name,
                "description": project.description,
            }
        )
        self._client.setex(
            self._key(project.id),
            self._ttl_seconds,
            payload,
        )

    def invalidate(self, project_id: int) -> None:
        self._client.delete(self._key(project_id))


class ResilientProjectCache:
    """Makes Redis an optimization instead of an availability dependency."""

    def __init__(self, cache: ProjectCache):
        self._cache = cache

    def get(self, project_id: int) -> Project | None:
        try:
            return self._cache.get(project_id)
        except (RedisError, ValueError, TypeError, KeyError, json.JSONDecodeError):
            logger.exception("Project cache read failed; falling back to PostgreSQL")
            return None

    def put(self, project: Project) -> None:
        try:
            self._cache.put(project)
        except (RedisError, ValueError, TypeError):
            logger.exception("Project cache write failed")

    def invalidate(self, project_id: int) -> None:
        try:
            self._cache.invalidate(project_id)
        except RedisError:
            logger.exception("Project cache invalidation failed")
