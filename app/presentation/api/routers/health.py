from fastapi import APIRouter, Depends

from app.application.use_cases.health import (
    CheckDatabaseHealth,
    CheckRedisHealth,
)
from app.bootstrap import (
    get_database_health_use_case,
    get_redis_health_use_case,
)

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/db")
def database_health_check(
    use_case: CheckDatabaseHealth = Depends(get_database_health_use_case),
) -> dict[str, str]:
    return {"status": "ok" if use_case.execute() else "error"}


@router.get("/redis")
def redis_health_check(
    use_case: CheckRedisHealth = Depends(get_redis_health_use_case),
) -> dict[str, str]:
    return {"status": "ok" if use_case.execute() else "error"}
