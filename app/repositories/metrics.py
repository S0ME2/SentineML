METRIC_COLUMNS = """
    id,
    run_id,
    name,
    value,
    notes
"""


def _get_metrics_for_update(run_id, db):
    cursor = db.execute(
        f"""
        SELECT {METRIC_COLUMNS}
        FROM metrics
        WHERE run_id = %s
        ORDER BY id
        FOR UPDATE;
        """,
        (run_id,),
    )

    return cursor.fetchall()


def get_metric_by_name(metric_name, db):
    cursor = db.execute(
        f"""
        SELECT {METRIC_COLUMNS}
        FROM metrics
        WHERE name = %s
        ORDER BY id
        LIMIT 1;
        """,
        (metric_name,),
    )

    return cursor.fetchone()


def get_metrics(run_id, db):
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


def create_metric(run_id, metric, db):
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

    return cursor.fetchone()


def update_metric(run_id, metric_id, update_fields, db):
    assignments = ", ".join(f"{column} = %s" for column in update_fields)
    values = tuple(update_fields.values())

    cursor = db.execute(
        f"""
        UPDATE metrics AS m
        SET {assignments}
        FROM runs AS r
        WHERE m.run_id = r.id
            AND m.id = %s
            AND m.run_id = %s
            AND r.status = 'running'
        RETURNING m.id, m.run_id, m.name, m.value, m.notes;
        """,
        values + (metric_id, run_id),
    )

    return cursor.fetchone()


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

    return cursor.fetchone()
