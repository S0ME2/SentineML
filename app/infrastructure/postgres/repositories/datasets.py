from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.application.exceptions import datasets as exc
from app.application.ports.repositories import DatasetRepository
from app.domain.datasets import Dataset
from app.infrastructure.postgres.integrity import (
    FOREIGN_KEY_VIOLATION,
    UNIQUE_VIOLATION,
    get_constraint_name,
    get_sqlstate,
)
from app.infrastructure.postgres.mappers.datasets import (
    apply_dataset_to_orm,
    dataset_to_domain,
    new_dataset_to_orm,
)
from app.infrastructure.postgres.orm_models.datasets import DatasetORM


class SQLAlchemyDatasetRepository(DatasetRepository):
    def __init__(self, session: Session):
        self._session = session

    def list_all(self) -> list[Dataset]:
        models = self._session.scalars(select(DatasetORM).order_by(DatasetORM.id)).all()
        return [dataset_to_domain(model) for model in models]

    def get_by_id(self, dataset_id: int) -> Dataset | None:
        model = self._session.get(DatasetORM, dataset_id)
        return None if model is None else dataset_to_domain(model)

    def get_by_id_for_update(self, dataset_id: int) -> Dataset | None:
        model = self._session.scalar(
            select(DatasetORM).where(DatasetORM.id == dataset_id).with_for_update()
        )
        return None if model is None else dataset_to_domain(model)

    def add(self, dataset: Dataset) -> Dataset:
        model = new_dataset_to_orm(dataset)
        self._session.add(model)
        try:
            self._session.flush()
        except IntegrityError as error:
            if (
                get_sqlstate(error) == UNIQUE_VIOLATION
                and get_constraint_name(error) == "uq_datasets_name_version"
            ):
                raise exc.DatasetAlreadyExists(
                    f"Dataset with the name '{dataset.name}' and version "
                    f"'{dataset.version}' already exists"
                ) from error
            raise
        return dataset_to_domain(model)

    def save(self, dataset: Dataset) -> Dataset:
        if dataset.id is None:
            raise ValueError("Cannot save a dataset without an id")
        model = self._session.get(DatasetORM, dataset.id)
        if model is None:
            raise RuntimeError("Dataset disappeared before it could be saved")
        apply_dataset_to_orm(dataset, model)
        try:
            self._session.flush()
        except IntegrityError as error:
            if (
                get_sqlstate(error) == UNIQUE_VIOLATION
                and get_constraint_name(error) == "uq_datasets_name_version"
            ):
                raise exc.DatasetAlreadyExists(
                    f"Dataset with the name '{dataset.name}' and version "
                    f"'{dataset.version}' already exists"
                ) from error
            raise
        return dataset_to_domain(model)

    def delete(self, dataset_id: int) -> None:
        model = self._session.get(DatasetORM, dataset_id)
        if model is None:
            raise RuntimeError("Dataset disappeared before it could be deleted")
        self._session.delete(model)
        try:
            self._session.flush()
        except IntegrityError as error:
            if (
                get_sqlstate(error) == FOREIGN_KEY_VIOLATION
                and get_constraint_name(error) == "fk_runs_dataset"
            ):
                raise exc.DatasetInUse(
                    f"Dataset with id {dataset_id} is used by existing runs and "
                    "cannot be deleted"
                ) from error
            raise
