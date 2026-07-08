from fastapi import HTTPException
from psycopg.errors import ForeignKeyViolation, UniqueViolation

DATASET_COLUMNS = """
    id,
    name,
    version,
    description,
    dataset_hash,
    source,
    metadata
"""


def _dataset_by_id(dataset_id, db):
    cursor = db.execute(
        f"""
        SELECT {DATASET_COLUMNS}
        FROM datasets
        WHERE id = %s;
        """,
        (dataset_id,),
    )

    return cursor.fetchone()


def _get_dataset_or_404(dataset_id, db):
    dataset = _dataset_by_id(dataset_id, db)

    if dataset is None:
        raise HTTPException(
            status_code=404,
            detail=f"Dataset with id {dataset_id} not found",
        )

    return dataset


def get_datasets(db):
    cursor = db.execute(
        f"""
        SELECT {DATASET_COLUMNS}
        FROM datasets
        ORDER BY id;
        """
    )

    return cursor.fetchall()


def get_dataset(dataset_id, db):
    return _get_dataset_or_404(dataset_id, db)


def create_dataset(dataset, db):
    try:
        cursor = db.execute(
            f"""
            INSERT INTO datasets (
                name,
                version,
                description,
                dataset_hash,
                source,
                metadata
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING {DATASET_COLUMNS};
            """,
            (
                dataset.name,
                dataset.version,
                dataset.description,
                dataset.dataset_hash,
                dataset.source,
                dataset.metadata,
            ),
        )

        created_dataset = cursor.fetchone()
        db.commit()
        return created_dataset

    except UniqueViolation:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail=(
                f"Dataset with the name '{dataset.name}' and version "
                f"'{dataset.version}' already exists"
            ),
        )


def update_dataset(dataset_id, dataset_update, db):
    existing_dataset = _get_dataset_or_404(dataset_id, db)

    update_fields = {
        "name": dataset_update.name,
        "version": dataset_update.version,
        "description": dataset_update.description,
        "dataset_hash": dataset_update.dataset_hash,
        "source": dataset_update.source,
        "metadata": dataset_update.metadata,
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
            UPDATE datasets
            SET {assignments}
            WHERE id = %s
            RETURNING {DATASET_COLUMNS};
            """,
            values + (dataset_id,),
        )

        updated_dataset = cursor.fetchone()
        db.commit()
        return updated_dataset

    except UniqueViolation:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail=(
                f"Dataset with the name '{dataset_update.name or existing_dataset['name']}' "
                f"and version '{dataset_update.version or existing_dataset['version']}' already exists"
            ),
        )


def delete_dataset(dataset_id, db):
    _get_dataset_or_404(dataset_id, db)

    try:
        db.execute(
            """
            DELETE FROM datasets
            WHERE id = %s;
            """,
            (dataset_id,),
        )
        db.commit()

    except ForeignKeyViolation:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail=f"Dataset with id {dataset_id} is used by existing runs and cannot be deleted",
        )
