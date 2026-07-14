from psycopg.errors import ForeignKeyViolation, UniqueViolation

from app.database import create_connection
from app.exceptions import models as exc
from app.repositories import models as models_crud
from app.services.common import build_update_fields


def _get_model_for_update(model_id, db):
    model = models_crud._model_by_id_for_update(model_id, db)

    if model is None:
        raise exc.ModelNotFound(f"Model with id {model_id} not found")

    return model


def get_models():
    db = create_connection()

    try:
        return models_crud.get_models(db)

    except Exception:
        raise

    finally:
        db.close()


def get_model(model_id):
    db = create_connection()

    try:
        model = models_crud.get_model(model_id, db)

        if model is None:
            raise exc.ModelNotFound(f"Model with id {model_id} not found")

        return model

    except Exception:
        raise

    finally:
        db.close()


def create_model(model):
    db = create_connection()

    try:
        created_model = models_crud.create_model(model, db)

        db.commit()
        return created_model

    except UniqueViolation:
        db.rollback()
        raise exc.ModelAlreadyExists(
            "Model with the name "
            f"'{model.name}' and version '{model.version}' already exists"
        )

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


def update_model(model_id, model_update):
    update_fields = build_update_fields(
        {
            "name": model_update.name,
            "version": model_update.version,
            "description": model_update.description,
            "model_type": model_update.model_type,
            "metadata": model_update.metadata,
        }
    )

    if not update_fields:
        raise exc.EmptyModelUpdate("No fields to update")

    db = create_connection()

    try:
        _get_model_for_update(model_id, db)

        updated_model = models_crud.update_model(model_id, update_fields, db)

        db.commit()
        return updated_model

    except UniqueViolation:
        db.rollback()
        raise exc.ModelAlreadyExists(
            "Model with the name "
            f"'{model_update.name}' and version "
            f"'{model_update.version}' already exists"
        )

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


def delete_model(model_id):
    db = create_connection()

    try:
        _get_model_for_update(model_id, db)

        models_crud.delete_model(model_id, db)
        db.commit()

    except ForeignKeyViolation:
        db.rollback()
        raise exc.ModelInUse(
            f"Model with id {model_id} is used by existing runs and cannot be deleted"
        )

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()
