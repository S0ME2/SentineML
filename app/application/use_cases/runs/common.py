from app.application.exceptions import runs as exc
from app.application.ports.unit_of_work import UnitOfWork
from app.domain.errors import InvalidRunData, InvalidRunState
from app.domain.runs import Run


def require_run(uow: UnitOfWork, run_id: int) -> Run:
    run = uow.runs.get_by_id(run_id)
    if run is None:
        raise exc.RunNotFound(f"Run with id {run_id} not found")
    return run


def require_run_for_update(uow: UnitOfWork, run_id: int) -> Run:
    run = uow.runs.get_by_id_for_update(run_id)
    if run is None:
        raise exc.RunNotFound(f"Run with id {run_id} not found")
    return run


def raise_run_error(error: InvalidRunData | InvalidRunState) -> None:
    if isinstance(error, InvalidRunState):
        raise exc.RunStatusError(str(error)) from error
    raise exc.InvalidRunData(str(error)) from error
