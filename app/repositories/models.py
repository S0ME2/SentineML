MODEL_COLUMNS = """
    id,
    name,
    version,
    description,
    model_type,
    metadata
"""


def _model_by_id_for_update(model_id, db):
    cursor = db.execute(
        f"""
        SELECT {MODEL_COLUMNS}
        FROM models
        WHERE id = %s
        FOR UPDATE;
        """,
        (model_id,),
    )

    return cursor.fetchone()


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
    cursor = db.execute(
        f"""
        SELECT {MODEL_COLUMNS}
        FROM models
        WHERE id = %s;
        """,
        (model_id,),
    )

    return cursor.fetchone()


def create_model(model, db):
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

    return cursor.fetchone()


def update_model(model_id, update_fields, db):
    assignments = ", ".join(f"{column} = %s" for column in update_fields)
    values = tuple(update_fields.values())

    cursor = db.execute(
        f"""
        UPDATE models
        SET {assignments}
        WHERE id = %s
        RETURNING {MODEL_COLUMNS};
        """,
        values + (model_id,),
    )

    return cursor.fetchone()


def delete_model(model_id, db):
    db.execute(
        """
        DELETE FROM models
        WHERE id = %s;
        """,
        (model_id,),
    )
