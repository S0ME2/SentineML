from fastapi import APIRouter, Depends

from app.database import get_db
from app.crud import runs as runs_crud
from app.schemas import runs as runs_schemas

router = APIRouter(prefix="/runs", tags=["runs"])


@router.get("/", response_model=list[runs_schemas.RunResponse])
def get_runs(db=Depends(get_db)):
    return runs_crud.get_runs(db)


@router.get("/{run_id}", response_model=runs_schemas.RunResponse)
def get_run(run_id: int, db=Depends(get_db)):
    return runs_crud.get_run(run_id, db)


@router.post("/", status_code=201, response_model=runs_schemas.RunResponse)
def create_run(run: runs_schemas.RunCreate, db=Depends(get_db)):
    return runs_crud.create_run(run, db)


@router.patch("/{run_id}", response_model=runs_schemas.RunResponse)
def update_run(run_id: int, run: runs_schemas.RunUpdate, db=Depends(get_db)):
    return runs_crud.update_run(run_id, run, db)


@router.delete("/{run_id}", status_code=204)
def delete_run(run_id: int, db=Depends(get_db)):
    return runs_crud.delete_run(run_id, db)


@router.post("/{run_id}/start", response_model=runs_schemas.RunResponse)
def start_run(run_id: int, db=Depends(get_db)):
    return runs_crud.start_run(run_id, db)


@router.post("/{run_id}/cancel", response_model=runs_schemas.RunResponse)
def cancel_run(run_id: int, reason: str | None = None, db=Depends(get_db)):
    return runs_crud.cancel_run(run_id, reason, db)


@router.post("/{run_id}/fail", response_model=runs_schemas.RunResponse)
def fail_run(run_id: int, reason: str, db=Depends(get_db)):
    return runs_crud.fail_run(run_id, reason, db)


@router.post("/{run_id}/ignore", response_model=runs_schemas.RunResponse)
def ignore_run(run_id: int, ignore_reason: str, db=Depends(get_db)):
    return runs_crud.ignore_run(run_id, ignore_reason, db)


@router.post("/{run_id}/unignore", response_model=runs_schemas.RunResponse)
def unignore_run(run_id: int, db=Depends(get_db)):
    return runs_crud.unignore_run(run_id, db)


@router.post("/{run_id}/complete", response_model=runs_schemas.RunResponse)
def complete_run(run_id: int, db=Depends(get_db)):
    return runs_crud.complete_run(run_id, db)
