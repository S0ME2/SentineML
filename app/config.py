import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv


def _load_environment() -> None:
    app_env = os.getenv("APP_ENV", "local")
    environment_file = Path(f".env.{app_env}")

    if environment_file.exists():
        load_dotenv(environment_file)
    else:
        load_dotenv()


_load_environment()


@dataclass(frozen=True, slots=True)
class Settings:
    database_url: str
    redis_url: str | None
    project_cache_ttl_seconds: int


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL environment variable is not set")

    redis_url = os.getenv("REDIS_URL") or None

    raw_ttl = os.getenv("PROJECT_CACHE_TTL_SECONDS", "300")
    try:
        cache_ttl = int(raw_ttl)
    except ValueError as error:
        raise RuntimeError("PROJECT_CACHE_TTL_SECONDS must be an integer") from error

    if cache_ttl <= 0:
        raise RuntimeError("PROJECT_CACHE_TTL_SECONDS must be greater than zero")

    return Settings(
        database_url=database_url,
        redis_url=redis_url,
        project_cache_ttl_seconds=cache_ttl,
    )
