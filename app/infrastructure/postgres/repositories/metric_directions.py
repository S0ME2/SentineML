from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.application.exceptions import metric_directions as exc
from app.application.ports.repositories import MetricDirectionRepository
from app.domain.metric_directions import MetricDirection
from app.infrastructure.postgres.integrity import (
    FOREIGN_KEY_VIOLATION,
    UNIQUE_VIOLATION,
    get_constraint_name,
    get_sqlstate,
)
from app.infrastructure.postgres.mappers.metric_directions import (
    apply_metric_direction_to_orm,
    metric_direction_to_domain,
    new_metric_direction_to_orm,
)
from app.infrastructure.postgres.orm_models.metric_directions import (
    MetricDirectionORM,
)


class SQLAlchemyMetricDirectionRepository(MetricDirectionRepository):
    def __init__(self, session: Session):
        self._session = session

    def list_all(self) -> list[MetricDirection]:
        models = self._session.scalars(
            select(MetricDirectionORM).order_by(MetricDirectionORM.name)
        ).all()
        return [metric_direction_to_domain(model) for model in models]

    def get_by_name(self, metric_name: str) -> MetricDirection | None:
        model = self._session.get(MetricDirectionORM, metric_name)
        return None if model is None else metric_direction_to_domain(model)

    def get_by_name_for_update(self, metric_name: str) -> MetricDirection | None:
        model = self._session.scalar(
            select(MetricDirectionORM)
            .where(MetricDirectionORM.name == metric_name)
            .with_for_update()
        )
        return None if model is None else metric_direction_to_domain(model)

    def add(self, metric_direction: MetricDirection) -> MetricDirection:
        model = new_metric_direction_to_orm(metric_direction)
        self._session.add(model)
        try:
            self._session.flush()
        except IntegrityError as error:
            if get_sqlstate(error) == UNIQUE_VIOLATION:
                raise exc.MetricDirectionAlreadyExists(
                    f"Metric direction '{metric_direction.name}' already exists"
                ) from error
            raise
        return metric_direction_to_domain(model)

    def save(self, metric_direction: MetricDirection) -> MetricDirection:
        model = self._session.get(MetricDirectionORM, metric_direction.name)
        if model is None:
            raise RuntimeError("Metric direction disappeared before it could be saved")
        apply_metric_direction_to_orm(metric_direction, model)
        self._session.flush()
        return metric_direction_to_domain(model)

    def delete(self, metric_name: str) -> None:
        model = self._session.get(MetricDirectionORM, metric_name)
        if model is None:
            raise RuntimeError(
                "Metric direction disappeared before it could be deleted"
            )
        self._session.delete(model)
        try:
            self._session.flush()
        except IntegrityError as error:
            if (
                get_sqlstate(error) == FOREIGN_KEY_VIOLATION
                and get_constraint_name(error) == "fk_metrics_direction"
            ):
                raise exc.MetricDirectionInUse(
                    f"Metric direction '{metric_name}' is used by existing metrics "
                    "and cannot be deleted"
                ) from error
            raise
