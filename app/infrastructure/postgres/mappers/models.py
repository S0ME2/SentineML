from app.domain.models import Model
from app.infrastructure.postgres.orm_models.models import ModelORM


def model_to_domain(model_orm: ModelORM) -> Model:
    return Model(
        id=model_orm.id,
        name=model_orm.name,
        version=model_orm.version,
        description=model_orm.description,
        model_type=model_orm.model_type,
        metadata=model_orm.metadata_value,
    )


def new_model_to_orm(model: Model) -> ModelORM:
    if model.id is not None:
        raise ValueError("A new model must not already have an id")
    return ModelORM(
        name=model.name,
        version=model.version,
        description=model.description,
        model_type=model.model_type,
        metadata_value=model.metadata,
    )


def apply_model_to_orm(model: Model, model_orm: ModelORM) -> None:
    if model.id is None or model.id != model_orm.id:
        raise ValueError("Domain and ORM model ids do not match")
    model_orm.name = model.name
    model_orm.version = model.version
    model_orm.description = model.description
    model_orm.model_type = model.model_type
    model_orm.metadata_value = model.metadata
