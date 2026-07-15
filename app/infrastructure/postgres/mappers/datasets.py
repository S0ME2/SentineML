from app.domain.datasets import Dataset
from app.infrastructure.postgres.orm_models.datasets import DatasetORM


def dataset_to_domain(dataset_orm: DatasetORM) -> Dataset:
    return Dataset(
        id=dataset_orm.id,
        name=dataset_orm.name,
        version=dataset_orm.version,
        description=dataset_orm.description,
        dataset_hash=dataset_orm.dataset_hash,
        source=dataset_orm.source,
        metadata=dataset_orm.metadata_value,
    )


def new_dataset_to_orm(dataset: Dataset) -> DatasetORM:
    if dataset.id is not None:
        raise ValueError("A new dataset must not already have an id")
    return DatasetORM(
        name=dataset.name,
        version=dataset.version,
        description=dataset.description,
        dataset_hash=dataset.dataset_hash,
        source=dataset.source,
        metadata_value=dataset.metadata,
    )


def apply_dataset_to_orm(dataset: Dataset, dataset_orm: DatasetORM) -> None:
    if dataset.id is None or dataset.id != dataset_orm.id:
        raise ValueError("Domain and ORM dataset ids do not match")
    dataset_orm.name = dataset.name
    dataset_orm.version = dataset.version
    dataset_orm.description = dataset.description
    dataset_orm.dataset_hash = dataset.dataset_hash
    dataset_orm.source = dataset.source
    dataset_orm.metadata_value = dataset.metadata
