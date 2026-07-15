from app.domain.metric_directions import MetricDirection
from app.infrastructure.postgres.orm_models.metric_directions import MetricDirectionORM


def metric_direction_to_domain(
    metric_direction_orm: MetricDirectionORM,
) -> MetricDirection:
    return MetricDirection(
        name=metric_direction_orm.name,
        maximize=metric_direction_orm.maximize,
    )


def new_metric_direction_to_orm(
    metric_direction: MetricDirection,
) -> MetricDirectionORM:
    return MetricDirectionORM(
        name=metric_direction.name,
        maximize=metric_direction.maximize,
    )


def apply_metric_direction_to_orm(
    metric_direction: MetricDirection,
    metric_direction_orm: MetricDirectionORM,
) -> None:
    if metric_direction.name != metric_direction_orm.name:
        raise ValueError("A metric direction cannot be renamed")
    metric_direction_orm.maximize = metric_direction.maximize
