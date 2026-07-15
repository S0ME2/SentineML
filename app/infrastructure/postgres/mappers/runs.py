from app.domain.runs import Run
from app.infrastructure.postgres.orm_models.runs import RunORM


def run_to_domain(run_orm: RunORM) -> Run:
    return Run(
        id=run_orm.id,
        project_id=run_orm.project_id,
        dataset_id=run_orm.dataset_id,
        model_id=run_orm.model_id,
        status=run_orm.status,
        start_time=run_orm.start_time,
        end_time=run_orm.end_time,
        notes=run_orm.notes,
        is_ignored=run_orm.is_ignored,
        ignore_reason=run_orm.ignore_reason,
        reason=run_orm.reason,
    )


def new_run_to_orm(run: Run) -> RunORM:
    if run.id is not None:
        raise ValueError("A new run must not already have an id")
    return RunORM(
        project_id=run.project_id,
        dataset_id=run.dataset_id,
        model_id=run.model_id,
        status=run.status,
        start_time=run.start_time,
        end_time=run.end_time,
        notes=run.notes,
        is_ignored=run.is_ignored,
        ignore_reason=run.ignore_reason,
        reason=run.reason,
    )


def apply_run_to_orm(run: Run, run_orm: RunORM) -> None:
    if run.id is None or run.id != run_orm.id:
        raise ValueError("Domain and ORM run ids do not match")
    run_orm.project_id = run.project_id
    run_orm.dataset_id = run.dataset_id
    run_orm.model_id = run.model_id
    run_orm.status = run.status
    run_orm.start_time = run.start_time
    run_orm.end_time = run.end_time
    run_orm.notes = run.notes
    run_orm.is_ignored = run.is_ignored
    run_orm.ignore_reason = run.ignore_reason
    run_orm.reason = run.reason
