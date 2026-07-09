PARAMETER_COLUMNS = """
    id,
    run_id,
    name,
    value,
    value_type,
    notes
"""


def _get_parameters_for_update(run_id, db):
    cursor = db.execute(
        f"""
        SELECT {PARAMETER_COLUMNS}
        FROM parameters
        WHERE run_id = %s
        ORDER BY id
        FOR UPDATE;
        """,
        (run_id,),
    )

    return cursor.fetchall()


def get_parameters(run_id, db):
    cursor = db.execute(
        f"""
        SELECT {PARAMETER_COLUMNS}
        FROM parameters
        WHERE run_id = %s
        ORDER BY id;
        """,
        (run_id,),
    )

    return cursor.fetchall()


def get_parameter(run_id, parameter_id, db):
    cursor = db.execute(
        f"""
        SELECT {PARAMETER_COLUMNS}
        FROM parameters
        WHERE run_id = %s
            AND id = %s;
        """,
        (run_id, parameter_id),
    )

    return cursor.fetchone()


def create_parameter(run_id, parameter, db):
    cursor = db.execute(
        f"""
        INSERT INTO parameters (run_id, name, value, value_type, notes)
        SELECT runs.id, %s, %s, %s, %s
        FROM runs
        WHERE runs.id = %s
            AND runs.status = 'waiting'
        RETURNING {PARAMETER_COLUMNS};
        """,
        (
            parameter.name,
            parameter.value,
            parameter.value_type,
            parameter.notes,
            run_id,
        ),
    )
    return cursor.fetchone()


def update_parameter(run_id, parameter_id, update_fields, db):
    assignments = ", ".join(f"{column} = %s" for column in update_fields)
    values = tuple(update_fields.values())

    cursor = db.execute(
        f"""
            UPDATE parameters AS p
            SET {assignments}
            FROM runs AS r
            WHERE p.run_id = r.id
                AND p.id = %s
                AND p.run_id = %s
                AND r.status = 'waiting'
            RETURNING p.id, p.run_id, p.name, p.value, p.value_type, p.notes;
        """,
        values + (parameter_id, run_id),
    )

    return cursor.fetchone()


def delete_parameter(run_id, parameter_id, db):
    cursor = db.execute(
        """
        DELETE FROM parameters AS p
        USING runs AS r
        WHERE p.run_id = r.id
            AND p.id = %s
            AND p.run_id = %s
            AND r.status = 'waiting'
        RETURNING p.id;
        """,
        (parameter_id, run_id),
    )

    return cursor.fetchone()
