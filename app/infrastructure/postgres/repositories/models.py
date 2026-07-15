from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.application.exceptions import models as exc
from app.application.ports.repositories import ModelRepository
from app.domain.models import Model
from app.infrastructure.postgres.integrity import (
    FOREIGN_KEY_VIOLATION,
    UNIQUE_VIOLATION,
    get_constraint_name,
    get_sqlstate,
)
from app.infrastructure.postgres.mappers.models import (
    apply_model_to_orm,
    model_to_domain,
    new_model_to_orm,
)
from app.infrastructure.postgres.orm_models.models import ModelORM


class SQLAlchemyModelRepository(ModelRepository):
    def __init__(self, session: Session):
        self._session = session

    def list_all(self) -> list[Model]:
        models = self._session.scalars(select(ModelORM).order_by(ModelORM.id)).all()
        return [model_to_domain(model) for model in models]

    def get_by_id(self, model_id: int) -> Model | None:
        model = self._session.get(ModelORM, model_id)
        return None if model is None else model_to_domain(model)

    def get_by_id_for_update(self, model_id: int) -> Model | None:
        model = self._session.scalar(
            select(ModelORM).where(ModelORM.id == model_id).with_for_update()
        )
        return None if model is None else model_to_domain(model)

    def add(self, model: Model) -> Model:
        model_orm = new_model_to_orm(model)
        self._session.add(model_orm)
        try:
            self._session.flush()
        except IntegrityError as error:
            if (
                get_sqlstate(error) == UNIQUE_VIOLATION
                and get_constraint_name(error) == "uq_models_name_version"
            ):
                raise exc.ModelAlreadyExists(
                    f"Model with the name '{model.name}' and version "
                    f"'{model.version}' already exists"
                ) from error
            raise
        return model_to_domain(model_orm)

    def save(self, model: Model) -> Model:
        if model.id is None:
            raise ValueError("Cannot save a model without an id")
        model_orm = self._session.get(ModelORM, model.id)
        if model_orm is None:
            raise RuntimeError("Model disappeared before it could be saved")
        apply_model_to_orm(model, model_orm)
        try:
            self._session.flush()
        except IntegrityError as error:
            if (
                get_sqlstate(error) == UNIQUE_VIOLATION
                and get_constraint_name(error) == "uq_models_name_version"
            ):
                raise exc.ModelAlreadyExists(
                    f"Model with the name '{model.name}' and version "
                    f"'{model.version}' already exists"
                ) from error
            raise
        return model_to_domain(model_orm)

    def delete(self, model_id: int) -> None:
        model = self._session.get(ModelORM, model_id)
        if model is None:
            raise RuntimeError("Model disappeared before it could be deleted")
        self._session.delete(model)
        try:
            self._session.flush()
        except IntegrityError as error:
            if (
                get_sqlstate(error) == FOREIGN_KEY_VIOLATION
                and get_constraint_name(error) == "fk_runs_model"
            ):
                raise exc.ModelInUse(
                    f"Model with id {model_id} is used by existing runs and "
                    "cannot be deleted"
                ) from error
            raise
