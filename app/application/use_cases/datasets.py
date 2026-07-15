from collections.abc import Mapping
from dataclasses import dataclass

from app.application.exceptions import datasets as exc
from app.application.ports.unit_of_work import UnitOfWorkFactory
from app.domain.datasets import Dataset
from app.domain.errors import InvalidDatasetData as DomainInvalidDatasetData


@dataclass(frozen=True, slots=True, kw_only=True)
class CreateDatasetCommand:
    name: str
    version: str
    description: str | None = None
    dataset_hash: str | None = None
    source: str | None = None
    metadata: str | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class UpdateDatasetCommand:
    dataset_id: int
    fields: Mapping[str, object]


def _apply_fields(dataset: Dataset, fields: Mapping[str, object]) -> None:
    if "name" in fields:
        dataset.rename(fields["name"])
    if "version" in fields:
        dataset.change_version(fields["version"])
    if "description" in fields:
        dataset.change_description(fields["description"])
    if "dataset_hash" in fields:
        dataset.change_dataset_hash(fields["dataset_hash"])
    if "source" in fields:
        dataset.change_source(fields["source"])
    if "metadata" in fields:
        dataset.change_metadata(fields["metadata"])


class ListDatasets:
    def __init__(self, uow_factory: UnitOfWorkFactory):
        self._uow_factory = uow_factory

    def execute(self) -> list[Dataset]:
        with self._uow_factory() as uow:
            return uow.datasets.list_all()


class GetDataset:
    def __init__(self, uow_factory: UnitOfWorkFactory):
        self._uow_factory = uow_factory

    def execute(self, dataset_id: int) -> Dataset:
        with self._uow_factory() as uow:
            dataset = uow.datasets.get_by_id(dataset_id)
            if dataset is None:
                raise exc.DatasetNotFound(f"Dataset with id {dataset_id} not found")
            return dataset


class CreateDataset:
    def __init__(self, uow_factory: UnitOfWorkFactory):
        self._uow_factory = uow_factory

    def execute(self, command: CreateDatasetCommand) -> Dataset:
        try:
            dataset = Dataset(
                name=command.name,
                version=command.version,
                description=command.description,
                dataset_hash=command.dataset_hash,
                source=command.source,
                metadata=command.metadata,
            )
        except DomainInvalidDatasetData as error:
            raise exc.InvalidDatasetData(str(error)) from error

        with self._uow_factory() as uow:
            created_dataset = uow.datasets.add(dataset)
            uow.commit()
            return created_dataset


class UpdateDataset:
    ALLOWED_FIELDS = {
        "name",
        "version",
        "description",
        "dataset_hash",
        "source",
        "metadata",
    }

    def __init__(self, uow_factory: UnitOfWorkFactory):
        self._uow_factory = uow_factory

    def execute(self, command: UpdateDatasetCommand) -> Dataset:
        fields = dict(command.fields)
        if not fields:
            raise exc.EmptyDatasetUpdate("No fields to update")

        unknown_fields = set(fields) - self.ALLOWED_FIELDS
        if unknown_fields:
            raise exc.InvalidDatasetData(
                f"Unsupported dataset fields: {sorted(unknown_fields)}"
            )

        with self._uow_factory() as uow:
            dataset = uow.datasets.get_by_id_for_update(command.dataset_id)
            if dataset is None:
                raise exc.DatasetNotFound(
                    f"Dataset with id {command.dataset_id} not found"
                )

            try:
                _apply_fields(dataset, fields)
            except DomainInvalidDatasetData as error:
                raise exc.InvalidDatasetData(str(error)) from error

            updated_dataset = uow.datasets.save(dataset)
            uow.commit()
            return updated_dataset


class DeleteDataset:
    def __init__(self, uow_factory: UnitOfWorkFactory):
        self._uow_factory = uow_factory

    def execute(self, dataset_id: int) -> None:
        with self._uow_factory() as uow:
            dataset = uow.datasets.get_by_id_for_update(dataset_id)
            if dataset is None:
                raise exc.DatasetNotFound(f"Dataset with id {dataset_id} not found")

            uow.datasets.delete(dataset_id)
            uow.commit()
