from fastapi import HTTPException
from psycopg.errors import ForeignKeyViolation, UniqueViolation

from app.crud.runs import _get_run_or_404

METRIC_COLUMNS = """
    id,
    run_id,
    name,
    value,
    notes
"""


def _metric_by_id(run_id, metric_id, db):
    cursor = db.execute(
        f"""
        SELECT {METRIC_COLUMNS}
        FROM metrics
        WHERE run_id = %s
          AND id = %s;
        """,
        (run_id, metric_id),
    )

    return cursor.fetchone()


def _get_metric_or_404(run_id, metric_id, db):
    metric = _metric_by_id(run_id, metric_id, db)

    if metric is None:
        raise HTTPException(
            status_code=404,
            detail=f"Metric with id {metric_id} not found for run with id {run_id}",
        )

    return metric


def get_metrics(run_id, db):
    _get_run_or_404(run_id, db)

    cursor = db.execute(
        f"""
        SELECT {METRIC_COLUMNS}
        FROM metrics
        WHERE run_id = %s
        ORDER BY id;
        """,
        (run_id,),
    )

    return cursor.fetchall()


def get_metric(run_id, metric_id, db):
    _get_run_or_404(run_id, db)
    return _get_metric_or_404(run_id, metric_id, db)


def create_metric(run_id, metric, db):
    try:
        cursor = db.execute(
            f"""
            INSERT INTO metrics (run_id, name, value, notes)
            SELECT runs.id, %s, %s, %s
            FROM runs
            WHERE runs.id = %s
              AND runs.status = 'running'
            RETURNING {METRIC_COLUMNS};
            """,
            (
                metric.name,
                metric.value,
                metric.notes,
                run_id,
            ),
        )

        created_metric = cursor.fetchone()

        if created_metric is None:
            db.rollback()
            run = _get_run_or_404(run_id, db)

            if run["status"] != "running":
                raise HTTPException(
                    status_code=400,
                    detail=f"Run with id {run_id} is not in 'running' status",
                )

        db.commit()
        return created_metric

    except UniqueViolation:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Metric with the same name already exists for this run",
        )

    except ForeignKeyViolation:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail=f"Metric direction '{metric.name}' must exist before logging this metric",
        )


def update_metric(run_id, metric_id, metric_update, db):
    update_fields = {
        "name": metric_update.name,
        "value": metric_update.value,
        "notes": metric_update.notes,
    }
    update_fields = {
        column: value for column, value in update_fields.items() if value is not None
    }

    if not update_fields:
        raise HTTPException(
            status_code=400,
            detail="No fields to update",
        )

    try:
        cursor = db.execute(
            """
            UPDATE metrics AS m
            SET
                name = COALESCE(%s, m.name),
                value = COALESCE(%s, m.value),
                notes = COALESCE(%s, m.notes)
            FROM runs AS r
            WHERE m.run_id = r.id
              AND m.id = %s
              AND m.run_id = %s
              AND r.status = 'running'
            RETURNING m.id, m.run_id, m.name, m.value, m.notes;
            """,
            (
                metric_update.name,
                metric_update.value,
                metric_update.notes,
                metric_id,
                run_id,
            ),
        )

        updated_metric = cursor.fetchone()

        if updated_metric is None:
            db.rollback()
            run = _get_run_or_404(run_id, db)

            if run["status"] != "running":
                raise HTTPException(
                    status_code=400,
                    detail=f"Run with id {run_id} is not in 'running' status",
                )

            _get_metric_or_404(run_id, metric_id, db)

        db.commit()
        return updated_metric

    except UniqueViolation:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Metric name already exists for this run",
        )

    except ForeignKeyViolation:
        db.rollback()
        metric_name = metric_update.name or "unknown"
        raise HTTPException(
            status_code=409,
            detail=f"Metric direction '{metric_name}' must exist before using this metric",
        )


def delete_metric(run_id, metric_id, db):
    cursor = db.execute(
        """
        DELETE FROM metrics AS m
        USING runs AS r
        WHERE m.run_id = r.id
          AND m.id = %s
          AND m.run_id = %s
          AND r.status = 'running'
        RETURNING m.id;
        """,
        (metric_id, run_id),
    )

    deleted_metric = cursor.fetchone()

    if deleted_metric is None:
        db.rollback()
        run = _get_run_or_404(run_id, db)

        if run["status"] != "running":
            raise HTTPException(
                status_code=400,
                detail=f"Run with id {run_id} is not in 'running' status",
            )

        _get_metric_or_404(run_id, metric_id, db)

    db.commit()
