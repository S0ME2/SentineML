from collections.abc import Mapping
from dataclasses import dataclass

from app.application.exceptions import models as exc
from app.application.ports.unit_of_work import UnitOfWorkFactory
from app.domain.errors import InvalidModelData as DomainInvalidModelData
from app.domain.models import Model


@dataclass(frozen=True, slots=True, kw_only=True)
class CreateModelCommand:
    name: str
    version: str
    description: str | None = None
    model_type: str | None = None
    metadata: str | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class UpdateModelCommand:
    model_id: int
    fields: Mapping[str, object]


def _apply_fields(model: Model, fields: Mapping[str, object]) -> None:
    if "name" in fields:
        model.rename(fields["name"])
    if "version" in fields:
        model.change_version(fields["version"])
    if "description" in fields:
        model.change_description(fields["description"])
    if "model_type" in fields:
        model.change_model_type(fields["model_type"])
    if "metadata" in fields:
        model.change_metadata(fields["metadata"])


class ListModels:
    def __init__(self, uow_factory: UnitOfWorkFactory):
        self._uow_factory = uow_factory

    def execute(self) -> list[Model]:
        with self._uow_factory() as uow:
            return uow.models.list_all()


class GetModel:
    def __init__(self, uow_factory: UnitOfWorkFactory):
        self._uow_factory = uow_factory

    def execute(self, model_id: int) -> Model:
        with self._uow_factory() as uow:
            model = uow.models.get_by_id(model_id)
            if model is None:
                raise exc.ModelNotFound(f"Model with id {model_id} not found")
            return model


class CreateModel:
    def __init__(self, uow_factory: UnitOfWorkFactory):
        self._uow_factory = uow_factory

    def execute(self, command: CreateModelCommand) -> Model:
        try:
            model = Model(
                name=command.name,
                version=command.version,
                description=command.description,
                model_type=command.model_type,
                metadata=command.metadata,
            )
        except DomainInvalidModelData as error:
            raise exc.InvalidModelData(str(error)) from error

        with self._uow_factory() as uow:
            created_model = uow.models.add(model)
            uow.commit()
            return created_model


class UpdateModel:
    ALLOWED_FIELDS = {"name", "version", "description", "model_type", "metadata"}

    def __init__(self, uow_factory: UnitOfWorkFactory):
        self._uow_factory = uow_factory

    def execute(self, command: UpdateModelCommand) -> Model:
        fields = dict(command.fields)
        if not fields:
            raise exc.EmptyModelUpdate("No fields to update")

        unknown_fields = set(fields) - self.ALLOWED_FIELDS
        if unknown_fields:
            raise exc.InvalidModelData(
                f"Unsupported model fields: {sorted(unknown_fields)}"
            )

        with self._uow_factory() as uow:
            model = uow.models.get_by_id_for_update(command.model_id)
            if model is None:
                raise exc.ModelNotFound(f"Model with id {command.model_id} not found")

            try:
                _apply_fields(model, fields)
            except DomainInvalidModelData as error:
                raise exc.InvalidModelData(str(error)) from error

            updated_model = uow.models.save(model)
            uow.commit()
            return updated_model


class DeleteModel:
    def __init__(self, uow_factory: UnitOfWorkFactory):
        self._uow_factory = uow_factory

    def execute(self, model_id: int) -> None:
        with self._uow_factory() as uow:
            model = uow.models.get_by_id_for_update(model_id)
            if model is None:
                raise exc.ModelNotFound(f"Model with id {model_id} not found")

            uow.models.delete(model_id)
            uow.commit()
