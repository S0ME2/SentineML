from psycopg.errors import ForeignKeyViolation, UniqueViolation

from app.exceptions import metric_directions as exc
from app.repositories import metric_directions as metric_directions_crud
from app.repositories import metrics as metrics_crud


def _get_metric_direction_for_update(metric_name, db):
    metric_direction = metric_directions_crud.get_metric_direction_for_update(
        metric_name, db
    )

    if metric_direction is None:
        raise exc.MetricDirectionNotFound(f"Metric direction '{metric_name}' not found")

    return metric_direction


def get_metric_directions(db):
    return metric_directions_crud.get_metric_directions(db)


def get_metric_direction(metric_name, db):
    metric_direction = metric_directions_crud.get_metric_direction(metric_name, db)

    if metric_direction is None:
        raise exc.MetricDirectionNotFound(f"Metric direction '{metric_name}' not found")

    return metric_direction


def create_metric_direction(metric_direction, db):
    try:
        created_metric_direction = metric_directions_crud.create_metric_direction(
            metric_direction, db
        )

        db.commit()
        return created_metric_direction

    except UniqueViolation:
        db.rollback()
        raise exc.MetricDirectionAlreadyExists(
            f"Metric direction '{metric_direction.name}' already exists"
        )

    except Exception:
        db.rollback()
        raise


def update_metric_direction(metric_name, metric_direction_update, db):
    try:
        _get_metric_direction_for_update(metric_name, db)

        if metrics_crud.get_metric_by_name(metric_name, db) is not None:
            raise exc.MetricDirectionInUse(
                "Metric direction "
                f"'{metric_name}' is already used by metrics and cannot be updated"
            )

        updated_metric_direction = metric_directions_crud.update_metric_direction(
            metric_name, metric_direction_update, db
        )

        db.commit()
        return updated_metric_direction

    except Exception:
        db.rollback()
        raise


def delete_metric_direction(metric_name, db):
    try:
        _get_metric_direction_for_update(metric_name, db)

        metric_directions_crud.delete_metric_direction(metric_name, db)

        db.commit()

    except ForeignKeyViolation:
        db.rollback()
        raise exc.MetricDirectionInUse(
            "Metric direction "
            f"'{metric_name}' is used by existing metrics and cannot be deleted"
        )

    except Exception:
        db.rollback()
        raise
