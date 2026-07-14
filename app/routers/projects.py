from fastapi import APIRouter, Depends

from app.database import get_db
from app.exceptions.base import AppError
from app.routers.error_handlers import raise_http_error
from app.schemas import projects as projects_schemas
from app.schemas import runs as runs_schemas
from app.services import projects as projects_services
from app.services import runs as runs_services

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("/", response_model=list[projects_schemas.ProjectResponse])
def get_projects():
    try:
        return projects_services.get_projects()
    except AppError as error:
        raise_http_error(error)


@router.get("/{project_id}", response_model=projects_schemas.ProjectResponse)
def get_project(project_id: int):
    try:
        return projects_services.get_project(project_id)
    except AppError as error:
        raise_http_error(error)


@router.post("/", status_code=201, response_model=projects_schemas.ProjectResponse)
def create_project(project: projects_schemas.ProjectCreate):
    try:
        return projects_services.create_project(project)
    except AppError as error:
        raise_http_error(error)


@router.patch("/{project_id}", response_model=projects_schemas.ProjectResponse)
def update_project(
    project_id: int, project: projects_schemas.ProjectUpdate
):
    try:
        return projects_services.update_project(project_id, project)
    except AppError as error:
        raise_http_error(error)


@router.delete("/{project_id}", status_code=204)
def delete_project(project_id: int):
    try:
        return projects_services.delete_project(project_id)
    except AppError as error:
        raise_http_error(error)


@router.get(
    "/{project_id}/best-run",
    response_model=runs_schemas.ProjectRunRankingItem,
)
def get_project_best_run(
    project_id: int,
    metric_name: str,
    db=Depends(get_db),
):
    try:
        return runs_services.get_project_best_run(project_id, metric_name, db)

    except AppError as error:
        raise_http_error(error)


@router.get(
    "/{project_id}/runs/compare",
    response_model=list[runs_schemas.ProjectRunRankingItem],
)
def compare_project_runs(
    project_id: int,
    metric_name: str,
    db=Depends(get_db),
):
    try:
        return runs_services.compare_project_runs(project_id, metric_name, db)

    except AppError as error:
        raise_http_error(error)
