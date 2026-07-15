from dataclasses import dataclass

from app.application.exceptions import runs as exc
from app.application.ports.clock import Clock
from app.application.ports.unit_of_work import UnitOfWorkFactory
from app.application.use_cases.runs.common import (
    raise_run_error,
    require_run_for_update,
)
from app.domain.errors import InvalidRunData, InvalidRunState
from app.domain.runs import Run


@dataclass(frozen=True, slots=True, kw_only=True)
class CancelRunCommand:
    run_id: int
    reason: str | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class FailRunCommand:
    run_id: int
    reason: str


@dataclass(frozen=True, slots=True, kw_only=True)
class IgnoreRunCommand:
    run_id: int
    reason: str


class StartRun:
    def __init__(self, uow_factory: UnitOfWorkFactory, clock: Clock):
        self._uow_factory = uow_factory
        self._clock = clock

    def execute(self, run_id: int) -> Run:
        with self._uow_factory() as uow:
            run = require_run_for_update(uow, run_id)
            try:
                run.ensure_can_start()
            except InvalidRunState as error:
                raise exc.RunStatusError(str(error)) from error

            if not uow.parameters.exists_for_run(run_id):
                raise exc.RunStatusError(
                    f"Run with id {run_id} cannot be started because it has "
                    "no parameters"
                )

            try:
                run.start(self._clock.now())
            except (InvalidRunData, InvalidRunState) as error:
                raise_run_error(error)

            started_run = uow.runs.save(run)
            uow.commit()
            return started_run


class CancelRun:
    def __init__(self, uow_factory: UnitOfWorkFactory, clock: Clock):
        self._uow_factory = uow_factory
        self._clock = clock

    def execute(self, command: CancelRunCommand) -> Run:
        with self._uow_factory() as uow:
            run = require_run_for_update(uow, command.run_id)
            try:
                run.cancel(command.reason, self._clock.now())
            except (InvalidRunData, InvalidRunState) as error:
                raise_run_error(error)

            cancelled_run = uow.runs.save(run)
            uow.commit()
            return cancelled_run


class FailRun:
    def __init__(self, uow_factory: UnitOfWorkFactory, clock: Clock):
        self._uow_factory = uow_factory
        self._clock = clock

    def execute(self, command: FailRunCommand) -> Run:
        with self._uow_factory() as uow:
            run = require_run_for_update(uow, command.run_id)
            try:
                run.fail(command.reason, self._clock.now())
            except (InvalidRunData, InvalidRunState) as error:
                raise_run_error(error)

            failed_run = uow.runs.save(run)
            uow.commit()
            return failed_run


class IgnoreRun:
    def __init__(self, uow_factory: UnitOfWorkFactory):
        self._uow_factory = uow_factory

    def execute(self, command: IgnoreRunCommand) -> Run:
        with self._uow_factory() as uow:
            run = require_run_for_update(uow, command.run_id)
            try:
                run.ignore(command.reason)
            except InvalidRunData as error:
                raise exc.InvalidRunData(str(error)) from error

            ignored_run = uow.runs.save(run)
            uow.commit()
            return ignored_run


class UnignoreRun:
    def __init__(self, uow_factory: UnitOfWorkFactory):
        self._uow_factory = uow_factory

    def execute(self, run_id: int) -> Run:
        with self._uow_factory() as uow:
            run = require_run_for_update(uow, run_id)
            run.unignore()
            unignored_run = uow.runs.save(run)
            uow.commit()
            return unignored_run


class CompleteRun:
    def __init__(self, uow_factory: UnitOfWorkFactory, clock: Clock):
        self._uow_factory = uow_factory
        self._clock = clock

    def execute(self, run_id: int) -> Run:
        with self._uow_factory() as uow:
            run = require_run_for_update(uow, run_id)
            try:
                run.ensure_can_complete()
            except InvalidRunState as error:
                raise exc.RunStatusError(str(error)) from error

            if not uow.metrics.exists_for_run(run_id):
                raise exc.RunStatusError(
                    f"Run with id {run_id} cannot be completed because it has "
                    "no metrics"
                )

            try:
                run.complete(self._clock.now())
            except (InvalidRunData, InvalidRunState) as error:
                raise_run_error(error)

            completed_run = uow.runs.save(run)
            uow.commit()
            return completed_run
