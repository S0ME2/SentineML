from types import TracebackType
from typing import Self

from sqlalchemy.orm import Session, sessionmaker

from app.application.ports.repositories import (
    DatasetRepository,
    MetricDirectionRepository,
    MetricRepository,
    ModelRepository,
    ParameterRepository,
    ProjectRepository,
    RunRepository,
)
from app.application.ports.unit_of_work import UnitOfWork
from app.infrastructure.postgres.repositories import (
    SQLAlchemyDatasetRepository,
    SQLAlchemyMetricDirectionRepository,
    SQLAlchemyMetricRepository,
    SQLAlchemyModelRepository,
    SQLAlchemyParameterRepository,
    SQLAlchemyProjectRepository,
    SQLAlchemyRunRepository,
)


class SQLAlchemyUnitOfWork(UnitOfWork):
    def __init__(self, session_factory: sessionmaker[Session]):
        self._session_factory = session_factory
        self._session: Session | None = None
        self._committed = False

        self.projects: ProjectRepository
        self.datasets: DatasetRepository
        self.models: ModelRepository
        self.runs: RunRepository
        self.parameters: ParameterRepository
        self.metrics: MetricRepository
        self.metric_directions: MetricDirectionRepository

    def __enter__(self) -> Self:
        if self._session is not None:
            raise RuntimeError("Unit of Work is already active")

        self._session = self._session_factory()
        self.projects = SQLAlchemyProjectRepository(self._session)
        self.datasets = SQLAlchemyDatasetRepository(self._session)
        self.models = SQLAlchemyModelRepository(self._session)
        self.runs = SQLAlchemyRunRepository(self._session)
        self.parameters = SQLAlchemyParameterRepository(self._session)
        self.metrics = SQLAlchemyMetricRepository(self._session)
        self.metric_directions = SQLAlchemyMetricDirectionRepository(self._session)
        self._committed = False
        return self

    def commit(self) -> None:
        if self._session is None:
            raise RuntimeError("Unit of Work is not active")
        self._session.commit()
        self._committed = True

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool:
        if self._session is None:
            return False

        try:
            if exc_type is not None or not self._committed:
                self._session.rollback()
        finally:
            self._session.close()
            self._session = None
            self._committed = False

        return False
