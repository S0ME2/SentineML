from fastapi import APIRouter, Depends

from app.database import get_db
from app.exceptions.base import AppError
from app.routers.error_handlers import raise_http_error
from app.schemas import runs as runs_schemas
from app.services import runs as runs_services

router = APIRouter(prefix="/runs", tags=["runs"])


@router.get("/", response_model=list[runs_schemas.RunResponse])
def get_runs(db=Depends(get_db)):
    try:
        return runs_services.get_runs(db)

    except AppError as error:
        raise_http_error(error)


@router.get("/{run_id}", response_model=runs_schemas.RunResponse)
def get_run(run_id: int, db=Depends(get_db)):
    try:
        return runs_services.get_run(run_id, db)

    except AppError as error:
        raise_http_error(error)


@router.post("/", status_code=201, response_model=runs_schemas.RunResponse)
def create_run(run: runs_schemas.RunCreate, db=Depends(get_db)):
    try:
        return runs_services.create_run(run, db)

    except AppError as error:
        raise_http_error(error)


@router.patch("/{run_id}", response_model=runs_schemas.RunResponse)
def update_run(run_id: int, run: runs_schemas.RunUpdate, db=Depends(get_db)):
    try:
        return runs_services.update_run(run_id, run, db)

    except AppError as error:
        raise_http_error(error)


@router.delete("/{run_id}", status_code=204)
def delete_run(run_id: int, db=Depends(get_db)):
    try:
        return runs_services.delete_run(run_id, db)

    except AppError as error:
        raise_http_error(error)


@router.post("/{run_id}/start", response_model=runs_schemas.RunResponse)
def start_run(run_id: int, db=Depends(get_db)):
    try:
        return runs_services.start_run(run_id, db)

    except AppError as error:
        raise_http_error(error)


@router.post("/{run_id}/cancel", response_model=runs_schemas.RunResponse)
def cancel_run(run_id: int, reason: str | None = None, db=Depends(get_db)):
    try:
        return runs_services.cancel_run(run_id, reason, db)

    except AppError as error:
        raise_http_error(error)


@router.post("/{run_id}/fail", response_model=runs_schemas.RunResponse)
def fail_run(run_id: int, reason: str, db=Depends(get_db)):
    try:
        return runs_services.fail_run(run_id, reason, db)

    except AppError as error:
        raise_http_error(error)


@router.post("/{run_id}/ignore", response_model=runs_schemas.RunResponse)
def ignore_run(run_id: int, ignore_reason: str, db=Depends(get_db)):
    try:
        return runs_services.ignore_run(run_id, ignore_reason, db)

    except AppError as error:
        raise_http_error(error)


@router.post("/{run_id}/unignore", response_model=runs_schemas.RunResponse)
def unignore_run(run_id: int, db=Depends(get_db)):
    try:
        return runs_services.unignore_run(run_id, db)

    except AppError as error:
        raise_http_error(error)


@router.post("/{run_id}/complete", response_model=runs_schemas.RunResponse)
def complete_run(run_id: int, db=Depends(get_db)):
    try:
        return runs_services.complete_run(run_id, db)

    except AppError as error:
        raise_http_error(error)
