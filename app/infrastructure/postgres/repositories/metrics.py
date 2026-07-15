from sqlalchemy import exists, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.application.exceptions import metric_directions as direction_exc
from app.application.exceptions import metrics as exc
from app.application.exceptions import runs as run_exc
from app.application.ports.repositories import MetricRepository
from app.domain.metrics import Metric
from app.infrastructure.postgres.integrity import (
    FOREIGN_KEY_VIOLATION,
    UNIQUE_VIOLATION,
    get_constraint_name,
    get_sqlstate,
)
from app.infrastructure.postgres.mappers.metrics import (
    apply_metric_to_orm,
    metric_to_domain,
    new_metric_to_orm,
)
from app.infrastructure.postgres.orm_models.metrics import MetricORM


class SQLAlchemyMetricRepository(MetricRepository):
    def __init__(self, session: Session):
        self._session = session

    def list_for_run(self, run_id: int) -> list[Metric]:
        models = self._session.scalars(
            select(MetricORM).where(MetricORM.run_id == run_id).order_by(MetricORM.id)
        ).all()
        return [metric_to_domain(model) for model in models]

    def get_for_run(self, run_id: int, metric_id: int) -> Metric | None:
        model = self._session.scalar(
            select(MetricORM).where(
                MetricORM.id == metric_id,
                MetricORM.run_id == run_id,
            )
        )
        return None if model is None else metric_to_domain(model)

    def get_for_run_for_update(
        self,
        run_id: int,
        metric_id: int,
    ) -> Metric | None:
        model = self._session.scalar(
            select(MetricORM)
            .where(MetricORM.id == metric_id, MetricORM.run_id == run_id)
            .with_for_update()
        )
        return None if model is None else metric_to_domain(model)

    def exists_for_run(self, run_id: int) -> bool:
        return bool(
            self._session.scalar(select(exists().where(MetricORM.run_id == run_id)))
        )

    def exists_by_name(self, metric_name: str) -> bool:
        return bool(
            self._session.scalar(select(exists().where(MetricORM.name == metric_name)))
        )

    def add(self, metric: Metric) -> Metric:
        model = new_metric_to_orm(metric)
        self._session.add(model)
        try:
            self._session.flush()
        except IntegrityError as error:
            self._translate_integrity_error(error, metric)
            raise
        return metric_to_domain(model)

    def save(self, metric: Metric) -> Metric:
        if metric.id is None:
            raise ValueError("Cannot save a metric without an id")
        model = self._session.get(MetricORM, metric.id)
        if model is None or model.run_id != metric.run_id:
            raise RuntimeError("Metric disappeared before it could be saved")
        apply_metric_to_orm(metric, model)
        try:
            self._session.flush()
        except IntegrityError as error:
            self._translate_integrity_error(error, metric)
            raise
        return metric_to_domain(model)

    def delete(self, run_id: int, metric_id: int) -> None:
        model = self._session.get(MetricORM, metric_id)
        if model is None or model.run_id != run_id:
            raise RuntimeError("Metric disappeared before it could be deleted")
        self._session.delete(model)
        self._session.flush()

    @staticmethod
    def _translate_integrity_error(error: IntegrityError, metric: Metric) -> None:
        constraint = get_constraint_name(error)
        if (
            get_sqlstate(error) == UNIQUE_VIOLATION
            and constraint == "uq_metrics_run_name"
        ):
            raise exc.MetricAlreadyExists(
                f"Metric with name '{metric.name}' already exists for run "
                f"with id {metric.run_id}"
            ) from error
        if get_sqlstate(error) == FOREIGN_KEY_VIOLATION:
            if constraint == "fk_metrics_direction":
                raise direction_exc.MetricDirectionNotFound(
                    f"Metric direction '{metric.name}' must exist before using "
                    "this metric"
                ) from error
            if constraint == "fk_metrics_run":
                raise run_exc.RunNotFound(
                    f"Run with id {metric.run_id} not found"
                ) from error
