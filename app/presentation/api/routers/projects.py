from fastapi import APIRouter, Depends, Response, status

from app.application.use_cases.projects import (
    CreateProject,
    CreateProjectCommand,
    DeleteProject,
    GetProject,
    ListProjects,
    UpdateProject,
    UpdateProjectCommand,
)
from app.application.use_cases.runs import CompareProjectRuns, GetProjectBestRun
from app.bootstrap import (
    get_compare_project_runs_use_case,
    get_create_project_use_case,
    get_delete_project_use_case,
    get_list_projects_use_case,
    get_project_best_run_use_case,
    get_project_use_case,
    get_update_project_use_case,
)
from app.presentation.api.schemas.projects import (
    ProjectCreate,
    ProjectResponse,
    ProjectUpdate,
)
from app.presentation.api.schemas.runs import ProjectRunRankingItem

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("/", response_model=list[ProjectResponse])
def list_projects(
    use_case: ListProjects = Depends(get_list_projects_use_case),
):
    return use_case.execute()


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: int,
    use_case: GetProject = Depends(get_project_use_case),
):
    return use_case.execute(project_id)


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=ProjectResponse)
def create_project(
    project: ProjectCreate,
    use_case: CreateProject = Depends(get_create_project_use_case),
):
    return use_case.execute(
        CreateProjectCommand(
            name=project.name,
            description=project.description,
        )
    )


@router.patch("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: int,
    project: ProjectUpdate,
    use_case: UpdateProject = Depends(get_update_project_use_case),
):
    return use_case.execute(
        UpdateProjectCommand(
            project_id=project_id,
            fields=project.model_dump(exclude_unset=True),
        )
    )


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: int,
    use_case: DeleteProject = Depends(get_delete_project_use_case),
) -> Response:
    use_case.execute(project_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{project_id}/best-run", response_model=ProjectRunRankingItem)
def get_project_best_run(
    project_id: int,
    metric_name: str,
    use_case: GetProjectBestRun = Depends(get_project_best_run_use_case),
):
    return use_case.execute(project_id, metric_name)


@router.get(
    "/{project_id}/runs/compare",
    response_model=list[ProjectRunRankingItem],
)
def compare_project_runs(
    project_id: int,
    metric_name: str,
    use_case: CompareProjectRuns = Depends(get_compare_project_runs_use_case),
):
    return use_case.execute(project_id, metric_name)
