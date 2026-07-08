from fastapi import HTTPException
from psycopg.errors import ForeignKeyViolation, UniqueViolation

MODEL_COLUMNS = """
    id,
    name,
    version,
    description,
    model_type,
    metadata
"""


def _model_by_id(model_id, db):
    cursor = db.execute(
        f"""
        SELECT {MODEL_COLUMNS}
        FROM models
        WHERE id = %s;
        """,
        (model_id,),
    )

    return cursor.fetchone()


def _get_model_or_404(model_id, db):
    model = _model_by_id(model_id, db)

    if model is None:
        raise HTTPException(
            status_code=404,
            detail=f"Model with id {model_id} not found",
        )

    return model


def get_models(db):
    cursor = db.execute(
        f"""
        SELECT {MODEL_COLUMNS}
        FROM models
        ORDER BY id;
        """
    )

    return cursor.fetchall()


def get_model(model_id, db):
    return _get_model_or_404(model_id, db)


def create_model(model, db):
    try:
        cursor = db.execute(
            f"""
            INSERT INTO models (
                name,
                version,
                description,
                model_type,
                metadata
            )
            VALUES (%s, %s, %s, %s, %s)
            RETURNING {MODEL_COLUMNS};
            """,
            (
                model.name,
                model.version,
                model.description,
                model.model_type,
                model.metadata,
            ),
        )

        created_model = cursor.fetchone()
        db.commit()
        return created_model

    except UniqueViolation:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail=(
                f"Model with the name '{model.name}' and version "
                f"'{model.version}' already exists"
            ),
        )


def update_model(model_id, model_update, db):
    existing_model = _get_model_or_404(model_id, db)

    update_fields = {
        "name": model_update.name,
        "version": model_update.version,
        "description": model_update.description,
        "model_type": model_update.model_type,
        "metadata": model_update.metadata,
    }
    update_fields = {
        column: value for column, value in update_fields.items() if value is not None
    }

    if not update_fields:
        raise HTTPException(
            status_code=400,
            detail="No fields to update",
        )

    assignments = ", ".join(f"{column} = %s" for column in update_fields)
    values = tuple(update_fields.values())

    try:
        cursor = db.execute(
            f"""
            UPDATE models
            SET {assignments}
            WHERE id = %s
            RETURNING {MODEL_COLUMNS};
            """,
            values + (model_id,),
        )

        updated_model = cursor.fetchone()
        db.commit()
        return updated_model

    except UniqueViolation:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail=(
                f"Model with the name '{model_update.name or existing_model['name']}' "
                f"and version '{model_update.version or existing_model['version']}' already exists"
            ),
        )


def delete_model(model_id, db):
    _get_model_or_404(model_id, db)

    try:
        db.execute(
            """
            DELETE FROM models
            WHERE id = %s;
            """,
            (model_id,),
        )
        db.commit()

    except ForeignKeyViolation:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail=f"Model with id {model_id} is used by existing runs and cannot be deleted",
        )
