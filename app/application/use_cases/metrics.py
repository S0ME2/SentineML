from collections.abc import Mapping
from dataclasses import dataclass

from app.application.exceptions import metric_directions as direction_exc
from app.application.exceptions import metrics as exc
from app.application.exceptions import runs as run_exc
from app.application.ports.unit_of_work import UnitOfWork, UnitOfWorkFactory
from app.domain.errors import InvalidMetricData as DomainInvalidMetricData
from app.domain.errors import InvalidRunState
from app.domain.metrics import Metric
from app.domain.runs import Run


@dataclass(frozen=True, slots=True, kw_only=True)
class CreateMetricCommand:
    run_id: int
    name: str
    value: float
    notes: str | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class UpdateMetricCommand:
    run_id: int
    metric_id: int
    fields: Mapping[str, object]


def _require_run(uow: UnitOfWork, run_id: int) -> Run:
    run = uow.runs.get_by_id(run_id)
    if run is None:
        raise run_exc.RunNotFound(f"Run with id {run_id} not found")
    return run


def _require_running_run(uow: UnitOfWork, run_id: int) -> Run:
    run = uow.runs.get_by_id_for_update(run_id)
    if run is None:
        raise run_exc.RunNotFound(f"Run with id {run_id} not found")

    try:
        run.ensure_metrics_can_change()
    except InvalidRunState as error:
        raise run_exc.RunStatusError(str(error)) from error

    return run


def _require_direction(uow: UnitOfWork, metric_name: object) -> str:
    if not isinstance(metric_name, str):
        raise exc.InvalidMetricData("Metric name must be a string")

    direction = uow.metric_directions.get_by_name(metric_name.strip())
    if direction is None:
        raise direction_exc.MetricDirectionNotFound(
            f"Metric direction '{metric_name}' must exist before using this metric"
        )
    return direction.name


def _apply_fields(metric: Metric, fields: Mapping[str, object]) -> None:
    if "name" in fields:
        metric.rename(fields["name"])
    if "value" in fields:
        metric.change_value(fields["value"])
    if "notes" in fields:
        metric.change_notes(fields["notes"])


class ListMetrics:
    def __init__(self, uow_factory: UnitOfWorkFactory):
        self._uow_factory = uow_factory

    def execute(self, run_id: int) -> list[Metric]:
        with self._uow_factory() as uow:
            _require_run(uow, run_id)
            return uow.metrics.list_for_run(run_id)


class GetMetric:
    def __init__(self, uow_factory: UnitOfWorkFactory):
        self._uow_factory = uow_factory

    def execute(self, run_id: int, metric_id: int) -> Metric:
        with self._uow_factory() as uow:
            _require_run(uow, run_id)
            metric = uow.metrics.get_for_run(run_id, metric_id)
            if metric is None:
                raise exc.MetricNotFound(
                    f"Metric with id {metric_id} not found for run with id {run_id}"
                )
            return metric


class CreateMetric:
    def __init__(self, uow_factory: UnitOfWorkFactory):
        self._uow_factory = uow_factory

    def execute(self, command: CreateMetricCommand) -> Metric:
        with self._uow_factory() as uow:
            _require_running_run(uow, command.run_id)
            _require_direction(uow, command.name)

            try:
                metric = Metric(
                    run_id=command.run_id,
                    name=command.name,
                    value=command.value,
                    notes=command.notes,
                )
            except DomainInvalidMetricData as error:
                raise exc.InvalidMetricData(str(error)) from error

            created_metric = uow.metrics.add(metric)
            uow.commit()
            return created_metric


class UpdateMetric:
    ALLOWED_FIELDS = {"name", "value", "notes"}

    def __init__(self, uow_factory: UnitOfWorkFactory):
        self._uow_factory = uow_factory

    def execute(self, command: UpdateMetricCommand) -> Metric:
        fields = dict(command.fields)
        if not fields:
            raise exc.EmptyMetricUpdate("No fields to update")

        unknown_fields = set(fields) - self.ALLOWED_FIELDS
        if unknown_fields:
            raise exc.InvalidMetricData(
                f"Unsupported metric fields: {sorted(unknown_fields)}"
            )

        with self._uow_factory() as uow:
            _require_running_run(uow, command.run_id)
            metric = uow.metrics.get_for_run_for_update(
                command.run_id,
                command.metric_id,
            )
            if metric is None:
                raise exc.MetricNotFound(
                    f"Metric with id {command.metric_id} not found for run "
                    f"with id {command.run_id}"
                )

            if "name" in fields:
                _require_direction(uow, fields["name"])

            try:
                _apply_fields(metric, fields)
            except DomainInvalidMetricData as error:
                raise exc.InvalidMetricData(str(error)) from error

            updated_metric = uow.metrics.save(metric)
            uow.commit()
            return updated_metric


class DeleteMetric:
    def __init__(self, uow_factory: UnitOfWorkFactory):
        self._uow_factory = uow_factory

    def execute(self, run_id: int, metric_id: int) -> None:
        with self._uow_factory() as uow:
            _require_running_run(uow, run_id)
            metric = uow.metrics.get_for_run_for_update(run_id, metric_id)
            if metric is None:
                raise exc.MetricNotFound(
                    f"Metric with id {metric_id} not found for run with id {run_id}"
                )

            uow.metrics.delete(run_id, metric_id)
            uow.commit()
