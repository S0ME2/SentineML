from psycopg.errors import ForeignKeyViolation, UniqueViolation

from app.exceptions import (
    metric_directions as metric_directions_exc,
)
from app.exceptions import (
    metrics as exc,
)
from app.exceptions import (
    runs as runs_exc,
)
from app.repositories import metrics as metrics_crud
from app.services import runs as runs_services
from app.services.common import build_update_fields, require_found, require_status


def get_metrics(run_id, db):
    runs_services.get_run(run_id, db)
    return metrics_crud.get_metrics(run_id, db)


def get_metric(run_id, metric_id, db):
    runs_services.get_run(run_id, db)
    return require_found(
        metrics_crud.get_metric(run_id, metric_id, db),
        exc.MetricNotFound(
            f"Metric with id {metric_id} not found for run with id {run_id}"
        ),
    )


def _get_metrics_for_update(run_id, db):
    return metrics_crud._get_metrics_for_update(run_id, db)


def create_metric(run_id, metric, db):
    try:
        run = runs_services._get_run_for_update(run_id, db)

        require_status(
            run["status"],
            {"running"},
            runs_exc.RunStatusError(f"Run with id {run_id} is not in 'running' status"),
        )

        created_metric = metrics_crud.create_metric(run_id, metric, db)

        db.commit()
        return created_metric

    except UniqueViolation:
        db.rollback()
        raise exc.MetricAlreadyExists(
            f"Metric with name '{metric.name}' already exists for run {run_id}"
        )

    except ForeignKeyViolation:
        db.rollback()
        raise metric_directions_exc.MetricDirectionNotFound(
            f"Metric direction '{metric.name}' must exist before logging this metric",
        )

    except Exception:
        db.rollback()
        raise


def update_metric(run_id, metric_id, metric_update, db):
    try:
        run = runs_services._get_run_for_update(run_id, db)

        require_status(
            run["status"],
            {"running"},
            runs_exc.RunStatusError(f"Run with id {run_id} is not in 'running' status"),
        )

        update_fields = build_update_fields(
            {
                "name": metric_update.name,
                "value": metric_update.value,
                "notes": metric_update.notes,
            }
        )

        if not update_fields:
            raise exc.EmptyMetricUpdate("No fields to update")

        updated_metric = metrics_crud.update_metric(
            run_id, metric_id, update_fields, db
        )

        require_found(
            updated_metric,
            exc.MetricNotFound(
                f"Metric with id {metric_id} not found for run with id {run_id}"
            ),
        )

        db.commit()
        return updated_metric

    except UniqueViolation:
        db.rollback()
        raise exc.MetricAlreadyExists("Metric name already exists for this run")

    except ForeignKeyViolation:
        db.rollback()
        raise metric_directions_exc.MetricDirectionNotFound(
            "Metric direction "
            f"'{metric_update.name}' must exist before using this metric"
        )

    except Exception:
        db.rollback()
        raise


def delete_metric(run_id, metric_id, db):
    try:
        run = runs_services._get_run_for_update(run_id, db)

        require_status(
            run["status"],
            {"running"},
            runs_exc.RunStatusError(f"Run with id {run_id} is not in 'running' status"),
        )

        deleted_metric = metrics_crud.delete_metric(run_id, metric_id, db)

        require_found(
            deleted_metric,
            exc.MetricNotFound(
                f"Metric with id {metric_id} not found for run with id {run_id}"
            ),
        )

        db.commit()

    except Exception:
        db.rollback()
        raise
