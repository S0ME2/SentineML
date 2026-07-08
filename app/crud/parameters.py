from fastapi import HTTPException
from psycopg.errors import UniqueViolation

from app.crud.runs import _get_run_or_404

PARAMETER_COLUMNS = """
    id,
    run_id,
    name,
    value,
    value_type,
    notes
"""


def _parameter_by_id(run_id, parameter_id, db):
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


def _get_parameter_or_404(run_id, parameter_id, db):
    parameter = _parameter_by_id(run_id, parameter_id, db)

    if parameter is None:
        raise HTTPException(
            status_code=404,
            detail=f"Parameter with id {parameter_id} not found for run with id {run_id}",
        )

    return parameter


def get_parameters(run_id, db):
    _get_run_or_404(run_id, db)

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
    _get_run_or_404(run_id, db)
    return _get_parameter_or_404(run_id, parameter_id, db)


def create_parameter(run_id, parameter, db):
    try:
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

        created_parameter = cursor.fetchone()

        if created_parameter is None:
            db.rollback()
            run = _get_run_or_404(run_id, db)

            if run["status"] != "waiting":
                raise HTTPException(
                    status_code=400,
                    detail=f"Run with id {run_id} is not in 'waiting' status",
                )

        db.commit()
        return created_parameter

    except UniqueViolation:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Parameter with the same name already exists for this run",
        )


def update_parameter(run_id, parameter_id, parameter_update, db):
    update_fields = {
        "name": parameter_update.name,
        "value": parameter_update.value,
        "value_type": parameter_update.value_type,
        "notes": parameter_update.notes,
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
            UPDATE parameters AS p
            SET
                name = COALESCE(%s, p.name),
                value = COALESCE(%s, p.value),
                value_type = COALESCE(%s, p.value_type),
                notes = COALESCE(%s, p.notes)
            FROM runs AS r
            WHERE p.run_id = r.id
              AND p.id = %s
              AND p.run_id = %s
              AND r.status = 'waiting'
            RETURNING p.id, p.run_id, p.name, p.value, p.value_type, p.notes;
            """,
            (
                parameter_update.name,
                parameter_update.value,
                parameter_update.value_type,
                parameter_update.notes,
                parameter_id,
                run_id,
            ),
        )

        updated_parameter = cursor.fetchone()

        if updated_parameter is None:
            db.rollback()
            run = _get_run_or_404(run_id, db)

            if run["status"] != "waiting":
                raise HTTPException(
                    status_code=400,
                    detail=f"Run with id {run_id} is not in 'waiting' status",
                )

            _get_parameter_or_404(run_id, parameter_id, db)

        db.commit()
        return updated_parameter

    except UniqueViolation:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Parameter name already exists for this run",
        )


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

    deleted_parameter = cursor.fetchone()

    if deleted_parameter is None:
        db.rollback()
        run = _get_run_or_404(run_id, db)

        if run["status"] != "waiting":
            raise HTTPException(
                status_code=400,
                detail=f"Run with id {run_id} is not in 'waiting' status",
            )

        _get_parameter_or_404(run_id, parameter_id, db)

    db.commit()
