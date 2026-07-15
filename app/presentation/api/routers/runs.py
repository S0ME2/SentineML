from fastapi import APIRouter, Depends, Response, status

from app.application.use_cases.runs import (
    CancelRun,
    CancelRunCommand,
    CompleteRun,
    CreateRun,
    CreateRunCommand,
    DeleteRun,
    FailRun,
    FailRunCommand,
    GetRun,
    IgnoreRun,
    IgnoreRunCommand,
    ListRuns,
    StartRun,
    UnignoreRun,
    UpdateRun,
    UpdateRunCommand,
)
from app.bootstrap import (
    get_cancel_run_use_case,
    get_complete_run_use_case,
    get_create_run_use_case,
    get_delete_run_use_case,
    get_fail_run_use_case,
    get_ignore_run_use_case,
    get_list_runs_use_case,
    get_run_use_case,
    get_start_run_use_case,
    get_unignore_run_use_case,
    get_update_run_use_case,
)
from app.presentation.api.schemas.runs import RunCreate, RunResponse, RunUpdate

router = APIRouter(prefix="/runs", tags=["runs"])


@router.get("/", response_model=list[RunResponse])
def list_runs(use_case: ListRuns = Depends(get_list_runs_use_case)):
    return use_case.execute()


@router.get("/{run_id}", response_model=RunResponse)
def get_run(
    run_id: int,
    use_case: GetRun = Depends(get_run_use_case),
):
    return use_case.execute(run_id)


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=RunResponse)
def create_run(
    run: RunCreate,
    use_case: CreateRun = Depends(get_create_run_use_case),
):
    return use_case.execute(
        CreateRunCommand(
            project_id=run.project_id,
            dataset_id=run.dataset_id,
            model_id=run.model_id,
            notes=run.notes,
        )
    )


@router.patch("/{run_id}", response_model=RunResponse)
def update_run(
    run_id: int,
    run: RunUpdate,
    use_case: UpdateRun = Depends(get_update_run_use_case),
):
    return use_case.execute(
        UpdateRunCommand(
            run_id=run_id,
            fields=run.model_dump(exclude_unset=True),
        )
    )


@router.delete("/{run_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_run(
    run_id: int,
    use_case: DeleteRun = Depends(get_delete_run_use_case),
) -> Response:
    use_case.execute(run_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{run_id}/start", response_model=RunResponse)
def start_run(
    run_id: int,
    use_case: StartRun = Depends(get_start_run_use_case),
):
    return use_case.execute(run_id)


@router.post("/{run_id}/cancel", response_model=RunResponse)
def cancel_run(
    run_id: int,
    reason: str | None = None,
    use_case: CancelRun = Depends(get_cancel_run_use_case),
):
    return use_case.execute(CancelRunCommand(run_id=run_id, reason=reason))


@router.post("/{run_id}/fail", response_model=RunResponse)
def fail_run(
    run_id: int,
    reason: str,
    use_case: FailRun = Depends(get_fail_run_use_case),
):
    return use_case.execute(FailRunCommand(run_id=run_id, reason=reason))


@router.post("/{run_id}/ignore", response_model=RunResponse)
def ignore_run(
    run_id: int,
    ignore_reason: str,
    use_case: IgnoreRun = Depends(get_ignore_run_use_case),
):
    return use_case.execute(IgnoreRunCommand(run_id=run_id, reason=ignore_reason))


@router.post("/{run_id}/unignore", response_model=RunResponse)
def unignore_run(
    run_id: int,
    use_case: UnignoreRun = Depends(get_unignore_run_use_case),
):
    return use_case.execute(run_id)


@router.post("/{run_id}/complete", response_model=RunResponse)
def complete_run(
    run_id: int,
    use_case: CompleteRun = Depends(get_complete_run_use_case),
):
    return use_case.execute(run_id)
