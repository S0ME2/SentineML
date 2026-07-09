METRIC_DIRECTION_COLUMNS = """
    name,
    maximize
"""


def get_metric_direction_for_update(metric_name, db):
    cursor = db.execute(
        f"""
        SELECT {METRIC_DIRECTION_COLUMNS}
        FROM metric_directions
        WHERE name = %s
        FOR UPDATE;
        """,
        (metric_name,),
    )

    return cursor.fetchone()


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
    cursor = db.execute(
        f"""
        SELECT {METRIC_DIRECTION_COLUMNS}
        FROM metric_directions
        WHERE name = %s;
        """,
        (metric_name,),
    )

    return cursor.fetchone()


def create_metric_direction(metric_direction, db):
    cursor = db.execute(
        f"""
        INSERT INTO metric_directions (name, maximize)
        VALUES (%s, %s)
        RETURNING {METRIC_DIRECTION_COLUMNS};
        """,
        (metric_direction.name, metric_direction.maximize),
    )

    return cursor.fetchone()


def update_metric_direction(metric_name, metric_direction_update, db):
    cursor = db.execute(
        f"""
        UPDATE metric_directions
        SET maximize = %s
        WHERE name = %s
        RETURNING {METRIC_DIRECTION_COLUMNS};
        """,
        (metric_direction_update.maximize, metric_name),
    )

    return cursor.fetchone()


def delete_metric_direction(metric_name, db):
    db.execute(
        """
        DELETE FROM metric_directions
        WHERE name = %s;
        """,
        (metric_name,),
    )
