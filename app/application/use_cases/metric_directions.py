from dataclasses import dataclass

from app.application.exceptions import metric_directions as exc
from app.application.ports.unit_of_work import UnitOfWorkFactory
from app.domain.errors import (
    InvalidMetricDirectionData as DomainInvalidMetricDirectionData,
)
from app.domain.metric_directions import MetricDirection


def _normalize_metric_name(metric_name: object) -> str:
    if not isinstance(metric_name, str):
        raise exc.InvalidMetricDirectionData("Metric direction name must be a string")
    normalized_name = metric_name.strip()
    if not normalized_name:
        raise exc.InvalidMetricDirectionData("Metric direction name cannot be empty")
    return normalized_name


@dataclass(frozen=True, slots=True, kw_only=True)
class CreateMetricDirectionCommand:
    name: str
    maximize: bool


@dataclass(frozen=True, slots=True, kw_only=True)
class UpdateMetricDirectionCommand:
    metric_name: str
    maximize: object


class ListMetricDirections:
    def __init__(self, uow_factory: UnitOfWorkFactory):
        self._uow_factory = uow_factory

    def execute(self) -> list[MetricDirection]:
        with self._uow_factory() as uow:
            return uow.metric_directions.list_all()


class GetMetricDirection:
    def __init__(self, uow_factory: UnitOfWorkFactory):
        self._uow_factory = uow_factory

    def execute(self, metric_name: str) -> MetricDirection:
        metric_name = _normalize_metric_name(metric_name)
        with self._uow_factory() as uow:
            direction = uow.metric_directions.get_by_name(metric_name)
            if direction is None:
                raise exc.MetricDirectionNotFound(
                    f"Metric direction '{metric_name}' not found"
                )
            return direction


class CreateMetricDirection:
    def __init__(self, uow_factory: UnitOfWorkFactory):
        self._uow_factory = uow_factory

    def execute(self, command: CreateMetricDirectionCommand) -> MetricDirection:
        try:
            direction = MetricDirection(
                name=command.name,
                maximize=command.maximize,
            )
        except DomainInvalidMetricDirectionData as error:
            raise exc.InvalidMetricDirectionData(str(error)) from error

        with self._uow_factory() as uow:
            created_direction = uow.metric_directions.add(direction)
            uow.commit()
            return created_direction


class UpdateMetricDirection:
    def __init__(self, uow_factory: UnitOfWorkFactory):
        self._uow_factory = uow_factory

    def execute(self, command: UpdateMetricDirectionCommand) -> MetricDirection:
        metric_name = _normalize_metric_name(command.metric_name)
        with self._uow_factory() as uow:
            direction = uow.metric_directions.get_by_name_for_update(metric_name)
            if direction is None:
                raise exc.MetricDirectionNotFound(
                    f"Metric direction '{metric_name}' not found"
                )

            if uow.metrics.exists_by_name(metric_name):
                raise exc.MetricDirectionInUse(
                    f"Metric direction '{metric_name}' is already used by "
                    "metrics and cannot be updated"
                )

            try:
                direction.change_maximize(command.maximize)
            except DomainInvalidMetricDirectionData as error:
                raise exc.InvalidMetricDirectionData(str(error)) from error

            updated_direction = uow.metric_directions.save(direction)
            uow.commit()
            return updated_direction


class DeleteMetricDirection:
    def __init__(self, uow_factory: UnitOfWorkFactory):
        self._uow_factory = uow_factory

    def execute(self, metric_name: str) -> None:
        metric_name = _normalize_metric_name(metric_name)
        with self._uow_factory() as uow:
            direction = uow.metric_directions.get_by_name_for_update(metric_name)
            if direction is None:
                raise exc.MetricDirectionNotFound(
                    f"Metric direction '{metric_name}' not found"
                )

            uow.metric_directions.delete(metric_name)
            uow.commit()
