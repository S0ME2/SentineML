from app.domain.metrics import Metric
from app.infrastructure.postgres.orm_models.metrics import MetricORM


def metric_to_domain(metric_orm: MetricORM) -> Metric:
    return Metric(
        id=metric_orm.id,
        run_id=metric_orm.run_id,
        name=metric_orm.name,
        value=metric_orm.value,
        notes=metric_orm.notes,
    )


def new_metric_to_orm(metric: Metric) -> MetricORM:
    if metric.id is not None:
        raise ValueError("A new metric must not already have an id")
    return MetricORM(
        run_id=metric.run_id,
        name=metric.name,
        value=metric.value,
        notes=metric.notes,
    )


def apply_metric_to_orm(metric: Metric, metric_orm: MetricORM) -> None:
    if metric.id is None or metric.id != metric_orm.id:
        raise ValueError("Domain and ORM metric ids do not match")
    if metric.run_id != metric_orm.run_id:
        raise ValueError("A metric cannot be moved to another run")
    metric_orm.name = metric.name
    metric_orm.value = metric.value
    metric_orm.notes = metric.notes
