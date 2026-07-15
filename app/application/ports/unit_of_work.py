from collections.abc import Callable
from types import TracebackType
from typing import Protocol, Self

from app.application.ports.repositories import (
    DatasetRepository,
    MetricDirectionRepository,
    MetricRepository,
    ModelRepository,
    ParameterRepository,
    ProjectRepository,
    RunRepository,
)


class UnitOfWork(Protocol):
    projects: ProjectRepository
    datasets: DatasetRepository
    models: ModelRepository
    runs: RunRepository
    parameters: ParameterRepository
    metrics: MetricRepository
    metric_directions: MetricDirectionRepository

    def __enter__(self) -> Self: ...

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool | None: ...

    def commit(self) -> None: ...


UnitOfWorkFactory = Callable[[], UnitOfWork]
