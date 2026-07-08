from fastapi import HTTPException
from psycopg.errors import ForeignKeyViolation

RUN_COLUMNS = """
    id,
    project_id,
    dataset_id,
    model_id,
    status,
    start_time,
    end_time,
    notes,
    is_ignored,
    ignore_reason,
    reason
"""


def _resource_exists(table_name, resource_id, db):
    if table_name == "projects":
        query = """
        SELECT 1
        FROM projects
        WHERE id = %s;
        """
    elif table_name == "datasets":
        query = """
        SELECT 1
        FROM datasets
        WHERE id = %s;
        """
    elif table_name == "models":
        query = """
        SELECT 1
        FROM models
        WHERE id = %s;
        """
    else:
        raise ValueError(f"Unsupported table name: {table_name}")

    cursor = db.execute(query, (resource_id,))
    return cursor.fetchone() is not None


def _validate_run_references(project_id, dataset_id, model_id, db):
    if not _resource_exists("projects", project_id, db):
        raise HTTPException(
            status_code=404,
            detail=f"Project with id {project_id} not found",
        )

    if not _resource_exists("datasets", dataset_id, db):
        raise HTTPException(
            status_code=404,
            detail=f"Dataset with id {dataset_id} not found",
        )

    if not _resource_exists("models", model_id, db):
        raise HTTPException(
            status_code=404,
            detail=f"Model with id {model_id} not found",
        )


def _metric_direction_by_name(metric_name, db):
    cursor = db.execute(
        """
        SELECT name, maximize
        FROM metric_directions
        WHERE name = %s;
        """,
        (metric_name,),
    )

    return cursor.fetchone()


def _project_exists(project_id, db):
    cursor = db.execute(
        """
        SELECT 1
        FROM projects
        WHERE id = %s;
        """,
        (project_id,),
    )

    return cursor.fetchone() is not None


def _run_has_parameters(run_id, db):
    cursor = db.execute(
        """
        SELECT 1
        FROM parameters
        WHERE run_id = %s
        LIMIT 1;
        """,
        (run_id,),
    )

    return cursor.fetchone() is not None


def _run_has_metrics(run_id, db):
    cursor = db.execute(
        """
        SELECT 1
        FROM metrics
        WHERE run_id = %s
        LIMIT 1;
        """,
        (run_id,),
    )

    return cursor.fetchone() is not None


def _run_by_id(run_id, db, lock=False):
    query = f"""
        SELECT {RUN_COLUMNS}
        FROM runs
        WHERE id = %s
    """

    if lock:
        query += " FOR UPDATE"

    cursor = db.execute(query, (run_id,))
    return cursor.fetchone()


def _get_run_or_404(run_id, db, lock=False):
    run = _run_by_id(run_id, db, lock=lock)

    if run is None:
        raise HTTPException(
            status_code=404,
            detail=f"Run with id {run_id} not found",
        )

    return run


def get_runs(db):
    cursor = db.execute(
        f"""
        SELECT {RUN_COLUMNS}
        FROM runs
        ORDER BY id;
        """
    )

    return cursor.fetchall()


def get_run(run_id, db):
    return _get_run_or_404(run_id, db)


def create_run(run, db):
    _validate_run_references(run.project_id, run.dataset_id, run.model_id, db)

    try:
        cursor = db.execute(
            f"""
            INSERT INTO runs (project_id, dataset_id, model_id, status, notes, is_ignored)
            VALUES (%s, %s, %s, 'waiting', %s, FALSE)
            RETURNING {RUN_COLUMNS};
            """,
            (run.project_id, run.dataset_id, run.model_id, run.notes),
        )

        created_run = cursor.fetchone()
        db.commit()
        return created_run

    except ForeignKeyViolation:
        db.rollback()
        raise HTTPException(
            status_code=404,
            detail="Project, dataset, or model not found",
        )


def update_run(run_id, run_update, db):
    run = _get_run_or_404(run_id, db, lock=True)

    update_fields = {}

    if run_update.dataset_id is not None:
        if run["status"] != "waiting":
            raise HTTPException(
                status_code=400,
                detail="Dataset can only be changed while the run is waiting",
            )
        if not _resource_exists("datasets", run_update.dataset_id, db):
            raise HTTPException(
                status_code=404,
                detail=f"Dataset with id {run_update.dataset_id} not found",
            )
        update_fields["dataset_id"] = run_update.dataset_id

    if run_update.model_id is not None:
        if run["status"] != "waiting":
            raise HTTPException(
                status_code=400,
                detail="Model can only be changed while the run is waiting",
            )
        if not _resource_exists("models", run_update.model_id, db):
            raise HTTPException(
                status_code=404,
                detail=f"Model with id {run_update.model_id} not found",
            )
        update_fields["model_id"] = run_update.model_id

    if run_update.notes is not None:
        update_fields["notes"] = run_update.notes

    if run_update.reason is not None:
        if run["status"] not in {"failed", "cancelled"}:
            raise HTTPException(
                status_code=400,
                detail="Reason can only be updated for failed or cancelled runs",
            )
        update_fields["reason"] = run_update.reason

    if not update_fields:
        raise HTTPException(
            status_code=400,
            detail="No fields to update",
        )

    assignments = ", ".join(f"{column} = %s" for column in update_fields)
    values = tuple(update_fields.values())

    cursor = db.execute(
        f"""
        UPDATE runs
        SET {assignments}
        WHERE id = %s
        RETURNING {RUN_COLUMNS};
        """,
        values + (run_id,),
    )

    updated_run = cursor.fetchone()
    db.commit()
    return updated_run


def delete_run(run_id, db):
    run = _get_run_or_404(run_id, db, lock=True)

    if run["status"] != "waiting":
        raise HTTPException(
            status_code=409,
            detail=(
                f"Run with id {run_id} cannot be deleted because its status is "
                f"'{run['status']}'. Only waiting runs can be deleted. Use ignore instead."
            ),
        )

    db.execute(
        """
        DELETE FROM runs
        WHERE id = %s;
        """,
        (run_id,),
    )
    db.commit()


def start_run(run_id, db):
    run = _get_run_or_404(run_id, db, lock=True)

    if run["status"] != "waiting":
        raise HTTPException(
            status_code=400,
            detail=(
                f"Run with id {run_id} cannot be started because it is in "
                f"'{run['status']}' status"
            ),
        )

    if not _run_has_parameters(run_id, db):
        raise HTTPException(
            status_code=400,
            detail="Run cannot be started because it has no parameters",
        )

    cursor = db.execute(
        f"""
        UPDATE runs
        SET status = 'running', start_time = NOW(), end_time = NULL
        WHERE id = %s
        RETURNING {RUN_COLUMNS};
        """,
        (run_id,),
    )

    started_run = cursor.fetchone()
    db.commit()
    return started_run


def cancel_run(run_id, reason, db):
    run = _get_run_or_404(run_id, db, lock=True)

    if run["status"] not in {"waiting", "running"}:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Run with id {run_id} cannot be canceled because it is in "
                f"'{run['status']}' status"
            ),
        )

    cursor = db.execute(
        f"""
        UPDATE runs
        SET status = 'cancelled', end_time = NOW(), reason = %s
        WHERE id = %s
        RETURNING {RUN_COLUMNS};
        """,
        (reason, run_id),
    )

    cancelled_run = cursor.fetchone()
    db.commit()
    return cancelled_run


def fail_run(run_id, reason, db):
    run = _get_run_or_404(run_id, db, lock=True)

    if run["status"] != "running":
        raise HTTPException(
            status_code=400,
            detail=(
                f"Run with id {run_id} cannot be failed because it is in "
                f"'{run['status']}' status"
            ),
        )

    cursor = db.execute(
        f"""
        UPDATE runs
        SET status = 'failed', end_time = NOW(), reason = %s
        WHERE id = %s
        RETURNING {RUN_COLUMNS};
        """,
        (reason, run_id),
    )

    failed_run = cursor.fetchone()
    db.commit()
    return failed_run


def ignore_run(run_id, ignore_reason, db):
    _get_run_or_404(run_id, db)

    cursor = db.execute(
        f"""
        UPDATE runs
        SET is_ignored = TRUE, ignore_reason = %s
        WHERE id = %s
        RETURNING {RUN_COLUMNS};
        """,
        (ignore_reason, run_id),
    )

    ignored_run = cursor.fetchone()
    db.commit()
    return ignored_run


def unignore_run(run_id, db):
    _get_run_or_404(run_id, db)

    cursor = db.execute(
        f"""
        UPDATE runs
        SET is_ignored = FALSE, ignore_reason = NULL
        WHERE id = %s
        RETURNING {RUN_COLUMNS};
        """,
        (run_id,),
    )

    unignored_run = cursor.fetchone()
    db.commit()
    return unignored_run


def complete_run(run_id, db):
    run = _get_run_or_404(run_id, db, lock=True)

    if run["status"] != "running":
        raise HTTPException(
            status_code=400,
            detail=(
                f"Run with id {run_id} cannot be completed because it is in "
                f"'{run['status']}' status"
            ),
        )

    if not _run_has_metrics(run_id, db):
        raise HTTPException(
            status_code=400,
            detail="Run cannot be completed because it has no metrics",
        )

    cursor = db.execute(
        f"""
        UPDATE runs
        SET status = 'completed', end_time = NOW()
        WHERE id = %s
        RETURNING {RUN_COLUMNS};
        """,
        (run_id,),
    )

    completed_run = cursor.fetchone()
    db.commit()
    return completed_run


def compare_project_runs(project_id, metric_name, db):
    if not _project_exists(project_id, db):
        raise HTTPException(
            status_code=404,
            detail=f"Project with id {project_id} not found",
        )

    metric_direction = _metric_direction_by_name(metric_name, db)

    if metric_direction is None:
        raise HTTPException(
            status_code=404,
            detail=f"Metric direction '{metric_name}' not found",
        )

    sort_direction = "DESC" if metric_direction["maximize"] else "ASC"

    cursor = db.execute(
        f"""
        SELECT
            r.id AS run_id,
            r.project_id,
            r.dataset_id,
            r.model_id,
            r.status,
            r.start_time,
            r.end_time,
            r.notes,
            m.name AS metric_name,
            m.value AS metric_value,
            md.maximize
        FROM runs AS r
        JOIN metrics AS m
            ON m.run_id = r.id
        JOIN metric_directions AS md
            ON md.name = m.name
        WHERE r.project_id = %s
          AND r.status = 'completed'
          AND r.is_ignored = FALSE
          AND m.name = %s
        ORDER BY m.value {sort_direction}, r.id ASC;
        """,
        (project_id, metric_name),
    )

    ranked_runs = cursor.fetchall()

    if not ranked_runs:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Project with id {project_id} has no completed, non-ignored runs "
                f"with metric '{metric_name}'"
            ),
        )

    return ranked_runs


def get_project_best_run(project_id, metric_name, db):
    ranked_runs = compare_project_runs(project_id, metric_name, db)
    return ranked_runs[0]
