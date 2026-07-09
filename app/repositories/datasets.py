DATASET_COLUMNS = """
    id,
    name,
    version,
    description,
    dataset_hash,
    source,
    metadata
"""


def _dataset_by_id_for_update(dataset_id, db):
    cursor = db.execute(
        f"""
        SELECT {DATASET_COLUMNS}
        FROM datasets
        WHERE id = %s
        FOR UPDATE;
        """,
        (dataset_id,),
    )

    return cursor.fetchone()


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
    cursor = db.execute(
        f"""
        SELECT {DATASET_COLUMNS}
        FROM datasets
        WHERE id = %s;
        """,
        (dataset_id,),
    )

    return cursor.fetchone()


def create_dataset(dataset, db):
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

    return cursor.fetchone()


def update_dataset(dataset_id, update_fields, db):
    assignments = ", ".join(f"{column} = %s" for column in update_fields)
    values = tuple(update_fields.values())

    cursor = db.execute(
        f"""
        UPDATE datasets
        SET {assignments}
        WHERE id = %s
        RETURNING {DATASET_COLUMNS};
        """,
        values + (dataset_id,),
    )

    return cursor.fetchone()


def delete_dataset(dataset_id, db):
    db.execute(
        """
        DELETE FROM datasets
        WHERE id = %s;
        """,
        (dataset_id,),
    )
