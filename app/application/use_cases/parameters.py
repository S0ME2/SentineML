from collections.abc import Mapping
from dataclasses import dataclass

from app.application.exceptions import parameters as exc
from app.application.exceptions import runs as run_exc
from app.application.ports.unit_of_work import UnitOfWork, UnitOfWorkFactory
from app.domain.errors import (
    InvalidParameterData as DomainInvalidParameterData,
)
from app.domain.errors import InvalidRunState
from app.domain.parameters import Parameter
from app.domain.runs import Run


@dataclass(frozen=True, slots=True, kw_only=True)
class CreateParameterCommand:
    run_id: int
    name: str
    value: str
    value_type: str | None = None
    notes: str | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class UpdateParameterCommand:
    run_id: int
    parameter_id: int
    fields: Mapping[str, object]


def _require_run(uow: UnitOfWork, run_id: int) -> Run:
    run = uow.runs.get_by_id(run_id)
    if run is None:
        raise run_exc.RunNotFound(f"Run with id {run_id} not found")
    return run


def _require_waiting_run(uow: UnitOfWork, run_id: int) -> Run:
    run = uow.runs.get_by_id_for_update(run_id)
    if run is None:
        raise run_exc.RunNotFound(f"Run with id {run_id} not found")

    try:
        run.ensure_parameters_can_change()
    except InvalidRunState as error:
        raise run_exc.RunStatusError(str(error)) from error

    return run


def _apply_fields(parameter: Parameter, fields: Mapping[str, object]) -> None:
    if "name" in fields:
        parameter.rename(fields["name"])
    if "value" in fields:
        parameter.change_value(fields["value"])
    if "value_type" in fields:
        parameter.change_value_type(fields["value_type"])
    if "notes" in fields:
        parameter.change_notes(fields["notes"])


class ListParameters:
    def __init__(self, uow_factory: UnitOfWorkFactory):
        self._uow_factory = uow_factory

    def execute(self, run_id: int) -> list[Parameter]:
        with self._uow_factory() as uow:
            _require_run(uow, run_id)
            return uow.parameters.list_for_run(run_id)


class GetParameter:
    def __init__(self, uow_factory: UnitOfWorkFactory):
        self._uow_factory = uow_factory

    def execute(self, run_id: int, parameter_id: int) -> Parameter:
        with self._uow_factory() as uow:
            _require_run(uow, run_id)
            parameter = uow.parameters.get_for_run(run_id, parameter_id)
            if parameter is None:
                raise exc.ParameterNotFound(
                    f"Parameter with id {parameter_id} not found for run "
                    f"with id {run_id}"
                )
            return parameter


class CreateParameter:
    def __init__(self, uow_factory: UnitOfWorkFactory):
        self._uow_factory = uow_factory

    def execute(self, command: CreateParameterCommand) -> Parameter:
        with self._uow_factory() as uow:
            _require_waiting_run(uow, command.run_id)

            try:
                parameter = Parameter(
                    run_id=command.run_id,
                    name=command.name,
                    value=command.value,
                    value_type=command.value_type,
                    notes=command.notes,
                )
            except DomainInvalidParameterData as error:
                raise exc.InvalidParameterData(str(error)) from error

            created_parameter = uow.parameters.add(parameter)
            uow.commit()
            return created_parameter


class UpdateParameter:
    ALLOWED_FIELDS = {"name", "value", "value_type", "notes"}

    def __init__(self, uow_factory: UnitOfWorkFactory):
        self._uow_factory = uow_factory

    def execute(self, command: UpdateParameterCommand) -> Parameter:
        fields = dict(command.fields)
        if not fields:
            raise exc.EmptyParameterUpdate("No fields to update")

        unknown_fields = set(fields) - self.ALLOWED_FIELDS
        if unknown_fields:
            raise exc.InvalidParameterData(
                f"Unsupported parameter fields: {sorted(unknown_fields)}"
            )

        with self._uow_factory() as uow:
            _require_waiting_run(uow, command.run_id)
            parameter = uow.parameters.get_for_run_for_update(
                command.run_id,
                command.parameter_id,
            )
            if parameter is None:
                raise exc.ParameterNotFound(
                    f"Parameter with id {command.parameter_id} not found for run "
                    f"with id {command.run_id}"
                )

            try:
                _apply_fields(parameter, fields)
            except DomainInvalidParameterData as error:
                raise exc.InvalidParameterData(str(error)) from error

            updated_parameter = uow.parameters.save(parameter)
            uow.commit()
            return updated_parameter


class DeleteParameter:
    def __init__(self, uow_factory: UnitOfWorkFactory):
        self._uow_factory = uow_factory

    def execute(self, run_id: int, parameter_id: int) -> None:
        with self._uow_factory() as uow:
            _require_waiting_run(uow, run_id)
            parameter = uow.parameters.get_for_run_for_update(run_id, parameter_id)
            if parameter is None:
                raise exc.ParameterNotFound(
                    f"Parameter with id {parameter_id} not found for run "
                    f"with id {run_id}"
                )

            uow.parameters.delete(run_id, parameter_id)
            uow.commit()
