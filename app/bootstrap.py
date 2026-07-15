from functools import lru_cache

from redis import Redis
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.application.ports.caches import ProjectCache
from app.application.ports.unit_of_work import UnitOfWork
from app.application.use_cases.datasets import (
    CreateDataset,
    DeleteDataset,
    GetDataset,
    ListDatasets,
    UpdateDataset,
)
from app.application.use_cases.health import (
    CheckDatabaseHealth,
    CheckRedisHealth,
)
from app.application.use_cases.metric_directions import (
    CreateMetricDirection,
    DeleteMetricDirection,
    GetMetricDirection,
    ListMetricDirections,
    UpdateMetricDirection,
)
from app.application.use_cases.metrics import (
    CreateMetric,
    DeleteMetric,
    GetMetric,
    ListMetrics,
    UpdateMetric,
)
from app.application.use_cases.models import (
    CreateModel,
    DeleteModel,
    GetModel,
    ListModels,
    UpdateModel,
)
from app.application.use_cases.parameters import (
    CreateParameter,
    DeleteParameter,
    GetParameter,
    ListParameters,
    UpdateParameter,
)
from app.application.use_cases.projects import (
    CreateProject,
    DeleteProject,
    GetProject,
    ListProjects,
    UpdateProject,
)
from app.application.use_cases.runs import (
    CancelRun,
    CompareProjectRuns,
    CompleteRun,
    CreateRun,
    DeleteRun,
    FailRun,
    GetProjectBestRun,
    GetRun,
    IgnoreRun,
    ListRuns,
    StartRun,
    UnignoreRun,
    UpdateRun,
)
from app.config import get_settings
from app.infrastructure.clock import SystemClock
from app.infrastructure.postgres.health import SQLAlchemyDatabaseHealthCheck
from app.infrastructure.postgres.session import (
    create_session_factory,
    create_sqlalchemy_engine,
)
from app.infrastructure.postgres.unit_of_work import SQLAlchemyUnitOfWork
from app.infrastructure.redis.health import RedisClientHealthCheck
from app.infrastructure.redis.project_cache import (
    NullProjectCache,
    RedisProjectCache,
    ResilientProjectCache,
)


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    return create_sqlalchemy_engine(get_settings().database_url)


@lru_cache(maxsize=1)
def get_session_factory() -> sessionmaker[Session]:
    return create_session_factory(get_engine())


def create_unit_of_work() -> UnitOfWork:
    return SQLAlchemyUnitOfWork(get_session_factory())


@lru_cache(maxsize=1)
def get_redis_client() -> Redis | None:
    redis_url = get_settings().redis_url
    if redis_url is None:
        return None
    return Redis.from_url(redis_url, decode_responses=True)


@lru_cache(maxsize=1)
def get_project_cache() -> ProjectCache:
    client = get_redis_client()
    if client is None:
        return NullProjectCache()

    redis_cache = RedisProjectCache(
        client,
        ttl_seconds=get_settings().project_cache_ttl_seconds,
    )
    return ResilientProjectCache(redis_cache)


@lru_cache(maxsize=1)
def get_clock() -> SystemClock:
    return SystemClock()


# Health
def get_database_health_use_case() -> CheckDatabaseHealth:
    return CheckDatabaseHealth(SQLAlchemyDatabaseHealthCheck(get_engine()))


def get_redis_health_use_case() -> CheckRedisHealth:
    return CheckRedisHealth(RedisClientHealthCheck(get_redis_client()))


# Projects
def get_list_projects_use_case() -> ListProjects:
    return ListProjects(create_unit_of_work)


def get_project_use_case() -> GetProject:
    return GetProject(create_unit_of_work, get_project_cache())


def get_create_project_use_case() -> CreateProject:
    return CreateProject(create_unit_of_work, get_project_cache())


def get_update_project_use_case() -> UpdateProject:
    return UpdateProject(create_unit_of_work, get_project_cache())


def get_delete_project_use_case() -> DeleteProject:
    return DeleteProject(create_unit_of_work, get_project_cache())


# Datasets
def get_list_datasets_use_case() -> ListDatasets:
    return ListDatasets(create_unit_of_work)


def get_dataset_use_case() -> GetDataset:
    return GetDataset(create_unit_of_work)


def get_create_dataset_use_case() -> CreateDataset:
    return CreateDataset(create_unit_of_work)


def get_update_dataset_use_case() -> UpdateDataset:
    return UpdateDataset(create_unit_of_work)


def get_delete_dataset_use_case() -> DeleteDataset:
    return DeleteDataset(create_unit_of_work)


# Models
def get_list_models_use_case() -> ListModels:
    return ListModels(create_unit_of_work)


def get_model_use_case() -> GetModel:
    return GetModel(create_unit_of_work)


def get_create_model_use_case() -> CreateModel:
    return CreateModel(create_unit_of_work)


def get_update_model_use_case() -> UpdateModel:
    return UpdateModel(create_unit_of_work)


def get_delete_model_use_case() -> DeleteModel:
    return DeleteModel(create_unit_of_work)


# Parameters
def get_list_parameters_use_case() -> ListParameters:
    return ListParameters(create_unit_of_work)


def get_parameter_use_case() -> GetParameter:
    return GetParameter(create_unit_of_work)


def get_create_parameter_use_case() -> CreateParameter:
    return CreateParameter(create_unit_of_work)


def get_update_parameter_use_case() -> UpdateParameter:
    return UpdateParameter(create_unit_of_work)


def get_delete_parameter_use_case() -> DeleteParameter:
    return DeleteParameter(create_unit_of_work)


# Metrics
def get_list_metrics_use_case() -> ListMetrics:
    return ListMetrics(create_unit_of_work)


def get_metric_use_case() -> GetMetric:
    return GetMetric(create_unit_of_work)


def get_create_metric_use_case() -> CreateMetric:
    return CreateMetric(create_unit_of_work)


def get_update_metric_use_case() -> UpdateMetric:
    return UpdateMetric(create_unit_of_work)


def get_delete_metric_use_case() -> DeleteMetric:
    return DeleteMetric(create_unit_of_work)


# Metric directions
def get_list_metric_directions_use_case() -> ListMetricDirections:
    return ListMetricDirections(create_unit_of_work)


def get_metric_direction_use_case() -> GetMetricDirection:
    return GetMetricDirection(create_unit_of_work)


def get_create_metric_direction_use_case() -> CreateMetricDirection:
    return CreateMetricDirection(create_unit_of_work)


def get_update_metric_direction_use_case() -> UpdateMetricDirection:
    return UpdateMetricDirection(create_unit_of_work)


def get_delete_metric_direction_use_case() -> DeleteMetricDirection:
    return DeleteMetricDirection(create_unit_of_work)


# Runs
def get_list_runs_use_case() -> ListRuns:
    return ListRuns(create_unit_of_work)


def get_run_use_case() -> GetRun:
    return GetRun(create_unit_of_work)


def get_create_run_use_case() -> CreateRun:
    return CreateRun(create_unit_of_work)


def get_update_run_use_case() -> UpdateRun:
    return UpdateRun(create_unit_of_work)


def get_delete_run_use_case() -> DeleteRun:
    return DeleteRun(create_unit_of_work)


def get_start_run_use_case() -> StartRun:
    return StartRun(create_unit_of_work, get_clock())


def get_cancel_run_use_case() -> CancelRun:
    return CancelRun(create_unit_of_work, get_clock())


def get_fail_run_use_case() -> FailRun:
    return FailRun(create_unit_of_work, get_clock())


def get_ignore_run_use_case() -> IgnoreRun:
    return IgnoreRun(create_unit_of_work)


def get_unignore_run_use_case() -> UnignoreRun:
    return UnignoreRun(create_unit_of_work)


def get_complete_run_use_case() -> CompleteRun:
    return CompleteRun(create_unit_of_work, get_clock())


def get_compare_project_runs_use_case() -> CompareProjectRuns:
    return CompareProjectRuns(create_unit_of_work)


def get_project_best_run_use_case() -> GetProjectBestRun:
    return GetProjectBestRun(get_compare_project_runs_use_case())
