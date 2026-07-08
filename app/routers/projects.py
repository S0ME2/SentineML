from fastapi import APIRouter, Depends

from app.database import get_db
from app.crud import projects as projects_crud
from app.crud import runs as runs_crud
from app.schemas import projects as projects_schemas
from app.schemas import runs as runs_schemas

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("/", response_model=list[projects_schemas.ProjectResponse])
def get_projects(db=Depends(get_db)):
    return projects_crud.get_projects(db)


@router.get("/{project_id}", response_model=projects_schemas.ProjectResponse)
def get_project(project_id: int, db=Depends(get_db)):
    return projects_crud.get_project(project_id, db)


@router.post("/", status_code=201, response_model=projects_schemas.ProjectResponse)
def create_project(project: projects_schemas.ProjectCreate, db=Depends(get_db)):
    return projects_crud.create_project(project, db)


@router.patch("/{project_id}", response_model=projects_schemas.ProjectResponse)
def update_project(
    project_id: int, project: projects_schemas.ProjectUpdate, db=Depends(get_db)
):
    return projects_crud.update_project(project_id, project, db)


@router.delete("/{project_id}", status_code=204)
def delete_project(project_id: int, db=Depends(get_db)):
    return projects_crud.delete_project(project_id, db)


@router.get(
    "/{project_id}/best-run",
    response_model=runs_schemas.ProjectRunRankingItem,
)
def get_project_best_run(
    project_id: int,
    metric_name: str,
    db=Depends(get_db),
):
    return runs_crud.get_project_best_run(project_id, metric_name, db)


@router.get(
    "/{project_id}/runs/compare",
    response_model=list[runs_schemas.ProjectRunRankingItem],
)
def compare_project_runs(
    project_id: int,
    metric_name: str,
    db=Depends(get_db),
):
    return runs_crud.compare_project_runs(project_id, metric_name, db)
