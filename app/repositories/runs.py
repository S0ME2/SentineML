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


def _run_by_id_for_update(run_id, db):
    cursor = db.execute(
        f"""
        SELECT {RUN_COLUMNS}
        FROM runs
        WHERE id = %s
        FOR UPDATE;
        """,
        (run_id,),
    )

    return cursor.fetchone()


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
    cursor = db.execute(
        f"""
        SELECT {RUN_COLUMNS}
        FROM runs
        WHERE id = %s;
        """,
        (run_id,),
    )

    return cursor.fetchone()


def create_run(run, db):
    cursor = db.execute(
        f"""
        INSERT INTO runs (project_id, dataset_id, model_id, status, notes, is_ignored)
        VALUES (%s, %s, %s, 'waiting', %s, FALSE)
        RETURNING {RUN_COLUMNS};
        """,
        (run.project_id, run.dataset_id, run.model_id, run.notes),
    )

    return cursor.fetchone()


def update_run(run_id, update_fields, db):
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

    return cursor.fetchone()


def delete_run(run_id, db):
    db.execute(
        """
        DELETE FROM runs
        WHERE id = %s;
        """,
        (run_id,),
    )


def start_run(run_id, db):
    cursor = db.execute(
        f"""
        UPDATE runs
        SET status = 'running', start_time = NOW(), end_time = NULL
        WHERE id = %s
        RETURNING {RUN_COLUMNS};
        """,
        (run_id,),
    )

    return cursor.fetchone()


def cancel_run(run_id, reason, db):
    cursor = db.execute(
        f"""
        UPDATE runs
        SET status = 'cancelled', end_time = NOW(), reason = %s
        WHERE id = %s
        RETURNING {RUN_COLUMNS};
        """,
        (reason, run_id),
    )

    return cursor.fetchone()


def fail_run(run_id, reason, db):
    cursor = db.execute(
        f"""
        UPDATE runs
        SET status = 'failed', end_time = NOW(), reason = %s
        WHERE id = %s
        RETURNING {RUN_COLUMNS};
        """,
        (reason, run_id),
    )

    return cursor.fetchone()


def ignore_run(run_id, ignore_reason, db):
    cursor = db.execute(
        f"""
        UPDATE runs
        SET is_ignored = TRUE, ignore_reason = %s
        WHERE id = %s
        RETURNING {RUN_COLUMNS};
        """,
        (ignore_reason, run_id),
    )

    return cursor.fetchone()


def unignore_run(run_id, db):
    cursor = db.execute(
        f"""
        UPDATE runs
        SET is_ignored = FALSE, ignore_reason = NULL
        WHERE id = %s
        RETURNING {RUN_COLUMNS};
        """,
        (run_id,),
    )

    return cursor.fetchone()


def complete_run(run_id, db):
    cursor = db.execute(
        f"""
        UPDATE runs
        SET status = 'completed', end_time = NOW()
        WHERE id = %s
        RETURNING {RUN_COLUMNS};
        """,
        (run_id,),
    )

    return cursor.fetchone()


def compare_project_runs(project_id, metric_name, sort_direction, db):
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

    return ranked_runs
