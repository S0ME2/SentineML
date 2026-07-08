from fastapi import HTTPException
from psycopg.errors import ForeignKeyViolation, UniqueViolation

METRIC_DIRECTION_COLUMNS = """
    name,
    maximize
"""


def _metric_direction_by_name(metric_name, db):
    cursor = db.execute(
        f"""
        SELECT {METRIC_DIRECTION_COLUMNS}
        FROM metric_directions
        WHERE name = %s;
        """,
        (metric_name,),
    )

    return cursor.fetchone()


def _metric_direction_is_used(metric_name, db):
    cursor = db.execute(
        """
        SELECT 1
        FROM metrics
        WHERE name = %s
        LIMIT 1;
        """,
        (metric_name,),
    )

    return cursor.fetchone() is not None


def _get_metric_direction_or_404(metric_name, db):
    metric_direction = _metric_direction_by_name(metric_name, db)

    if metric_direction is None:
        raise HTTPException(
            status_code=404,
            detail=f"Metric direction '{metric_name}' not found",
        )

    return metric_direction


def get_metric_directions(db):
    cursor = db.execute(
        f"""
        SELECT {METRIC_DIRECTION_COLUMNS}
        FROM metric_directions
        ORDER BY name;
        """
    )

    return cursor.fetchall()


def get_metric_direction(metric_name, db):
    return _get_metric_direction_or_404(metric_name, db)


def create_metric_direction(metric_direction, db):
    try:
        cursor = db.execute(
            f"""
            INSERT INTO metric_directions (name, maximize)
            VALUES (%s, %s)
            RETURNING {METRIC_DIRECTION_COLUMNS};
            """,
            (metric_direction.name, metric_direction.maximize),
        )

        created_metric_direction = cursor.fetchone()
        db.commit()
        return created_metric_direction

    except UniqueViolation:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail=f"Metric direction '{metric_direction.name}' already exists",
        )


def update_metric_direction(metric_name, metric_direction_update, db):
    existing_metric_direction = _get_metric_direction_or_404(metric_name, db)

    if _metric_direction_is_used(metric_name, db):
        raise HTTPException(
            status_code=409,
            detail=(
                f"Metric direction '{metric_name}' is already used by metrics and cannot be updated"
            ),
        )

    cursor = db.execute(
        f"""
        UPDATE metric_directions
        SET maximize = %s
        WHERE name = %s
        RETURNING {METRIC_DIRECTION_COLUMNS};
        """,
        (metric_direction_update.maximize, metric_name),
    )

    updated_metric_direction = cursor.fetchone()
    db.commit()
    return updated_metric_direction or existing_metric_direction


def delete_metric_direction(metric_name, db):
    _get_metric_direction_or_404(metric_name, db)

    try:
        db.execute(
            """
            DELETE FROM metric_directions
            WHERE name = %s;
            """,
            (metric_name,),
        )
        db.commit()

    except ForeignKeyViolation:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail=(
                f"Metric direction '{metric_name}' is used by existing metrics and cannot be deleted"
            ),
        )
