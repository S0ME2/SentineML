from psycopg.errors import ForeignKeyViolation, UniqueViolation

from app.database import create_connection
from app.exceptions import datasets as exc
from app.repositories import datasets as datasets_crud
from app.services.common import build_update_fields


def _get_dataset_for_update(dataset_id, db):
    dataset = datasets_crud._dataset_by_id_for_update(dataset_id, db)

    if dataset is None:
        raise exc.DatasetNotFound(f"Dataset with id {dataset_id} not found")

    return dataset


def get_datasets():
    db = create_connection()

    try:
        return datasets_crud.get_datasets(db)

    except Exception:
        raise

    finally:
        db.close()


def get_dataset(dataset_id):
    db = create_connection()

    try:
        dataset = datasets_crud.get_dataset(dataset_id, db)

        if dataset is None:
            raise exc.DatasetNotFound(f"Dataset with id {dataset_id} not found")

        return dataset

    except Exception:
        raise

    finally:
        db.close()


def create_dataset(dataset):
    db = create_connection()

    try:
        created_dataset = datasets_crud.create_dataset(dataset, db)

        db.commit()
        return created_dataset

    except UniqueViolation:
        db.rollback()
        raise exc.DatasetAlreadyExists(
            "Dataset with the name "
            f"'{dataset.name}' and version '{dataset.version}' already exists"
        )

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


def update_dataset(dataset_id, dataset_update):
    update_fields = build_update_fields(
        {
            "name": dataset_update.name,
            "version": dataset_update.version,
            "description": dataset_update.description,
            "dataset_hash": dataset_update.dataset_hash,
            "source": dataset_update.source,
            "metadata": dataset_update.metadata,
        }
    )

    if not update_fields:
        raise exc.EmptyDatasetUpdate("No fields to update")

    db = create_connection()

    try:
        _get_dataset_for_update(dataset_id, db)

        updated_dataset = datasets_crud.update_dataset(dataset_id, update_fields, db)

        db.commit()
        return updated_dataset

    except UniqueViolation:
        db.rollback()
        raise exc.DatasetAlreadyExists(
            "Dataset with the name "
            f"'{dataset_update.name}' and version "
            f"'{dataset_update.version}' already exists"
        )

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


def delete_dataset(dataset_id):
    db = create_connection()

    try:
        _get_dataset_for_update(dataset_id, db)

        datasets_crud.delete_dataset(dataset_id, db)
        db.commit()

    except ForeignKeyViolation:
        db.rollback()
        raise exc.DatasetInUse(
            f"Dataset with id {dataset_id} is used by existing runs "
            "and cannot be deleted"
        )

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()
