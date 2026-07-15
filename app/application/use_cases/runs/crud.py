from collections.abc import Mapping
from dataclasses import dataclass

from app.application.exceptions import datasets as dataset_exc
from app.application.exceptions import models as model_exc
from app.application.exceptions import projects as project_exc
from app.application.exceptions import runs as exc
from app.application.ports.unit_of_work import UnitOfWork, UnitOfWorkFactory
from app.application.use_cases.runs.common import (
    raise_run_error,
    require_run_for_update,
)
from app.domain.errors import InvalidRunData, InvalidRunState
from app.domain.runs import Run


@dataclass(frozen=True, slots=True, kw_only=True)
class CreateRunCommand:
    project_id: int
    dataset_id: int
    model_id: int
    notes: str | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class UpdateRunCommand:
    run_id: int
    fields: Mapping[str, object]


def _require_references(
    uow: UnitOfWork,
    *,
    project_id: int,
    dataset_id: int,
    model_id: int,
) -> None:
    if uow.projects.get_by_id_for_update(project_id) is None:
        raise project_exc.ProjectNotFound(f"Project with id {project_id} not found")
    if uow.datasets.get_by_id_for_update(dataset_id) is None:
        raise dataset_exc.DatasetNotFound(f"Dataset with id {dataset_id} not found")
    if uow.models.get_by_id_for_update(model_id) is None:
        raise model_exc.ModelNotFound(f"Model with id {model_id} not found")


class ListRuns:
    def __init__(self, uow_factory: UnitOfWorkFactory):
        self._uow_factory = uow_factory

    def execute(self) -> list[Run]:
        with self._uow_factory() as uow:
            return uow.runs.list_all()


class GetRun:
    def __init__(self, uow_factory: UnitOfWorkFactory):
        self._uow_factory = uow_factory

    def execute(self, run_id: int) -> Run:
        with self._uow_factory() as uow:
            run = uow.runs.get_by_id(run_id)
            if run is None:
                raise exc.RunNotFound(f"Run with id {run_id} not found")
            return run


class CreateRun:
    def __init__(self, uow_factory: UnitOfWorkFactory):
        self._uow_factory = uow_factory

    def execute(self, command: CreateRunCommand) -> Run:
        with self._uow_factory() as uow:
            _require_references(
                uow,
                project_id=command.project_id,
                dataset_id=command.dataset_id,
                model_id=command.model_id,
            )

            try:
                run = Run(
                    project_id=command.project_id,
                    dataset_id=command.dataset_id,
                    model_id=command.model_id,
                    notes=command.notes,
                )
            except InvalidRunData as error:
                raise exc.InvalidRunData(str(error)) from error

            created_run = uow.runs.add(run)
            uow.commit()
            return created_run


class UpdateRun:
    ALLOWED_FIELDS = {"dataset_id", "model_id", "notes", "reason"}

    def __init__(self, uow_factory: UnitOfWorkFactory):
        self._uow_factory = uow_factory

    def execute(self, command: UpdateRunCommand) -> Run:
        fields = dict(command.fields)
        if not fields:
            raise exc.EmptyRunUpdate("No fields to update")

        unknown_fields = set(fields) - self.ALLOWED_FIELDS
        if unknown_fields:
            raise exc.InvalidRunData(
                f"Unsupported run fields: {sorted(unknown_fields)}"
            )

        with self._uow_factory() as uow:
            run = require_run_for_update(uow, command.run_id)

            try:
                if "dataset_id" in fields:
                    dataset_id = fields["dataset_id"]
                    if not isinstance(dataset_id, int) or isinstance(dataset_id, bool):
                        raise InvalidRunData("Run dataset_id must be an integer")
                    run.change_dataset(dataset_id)
                    if uow.datasets.get_by_id_for_update(dataset_id) is None:
                        raise dataset_exc.DatasetNotFound(
                            f"Dataset with id {dataset_id} not found"
                        )

                if "model_id" in fields:
                    model_id = fields["model_id"]
                    if not isinstance(model_id, int) or isinstance(model_id, bool):
                        raise InvalidRunData("Run model_id must be an integer")
                    run.change_model(model_id)
                    if uow.models.get_by_id_for_update(model_id) is None:
                        raise model_exc.ModelNotFound(
                            f"Model with id {model_id} not found"
                        )

                if "notes" in fields:
                    run.change_notes(fields["notes"])

                if "reason" in fields:
                    run.update_reason(fields["reason"])

            except (InvalidRunData, InvalidRunState) as error:
                raise_run_error(error)

            updated_run = uow.runs.save(run)
            uow.commit()
            return updated_run


class DeleteRun:
    def __init__(self, uow_factory: UnitOfWorkFactory):
        self._uow_factory = uow_factory

    def execute(self, run_id: int) -> None:
        with self._uow_factory() as uow:
            run = require_run_for_update(uow, run_id)
            try:
                run.ensure_can_be_deleted()
            except InvalidRunState as error:
                raise exc.RunStatusError(str(error)) from error

            uow.runs.delete(run_id)
            uow.commit()
