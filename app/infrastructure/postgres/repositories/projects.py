from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.application.exceptions import projects as exc
from app.application.ports.repositories import ProjectRepository
from app.domain.projects import Project
from app.infrastructure.postgres.integrity import (
    FOREIGN_KEY_VIOLATION,
    UNIQUE_VIOLATION,
    get_constraint_name,
    get_sqlstate,
)
from app.infrastructure.postgres.mappers.projects import (
    apply_project_to_orm,
    new_project_to_orm,
    project_to_domain,
)
from app.infrastructure.postgres.orm_models.projects import ProjectORM

PROJECT_NAME_CONSTRAINTS = {"uq_projects_name", "projects_name_key"}


class SQLAlchemyProjectRepository(ProjectRepository):
    def __init__(self, session: Session):
        self._session = session

    def list_all(self) -> list[Project]:
        models = self._session.scalars(select(ProjectORM).order_by(ProjectORM.id)).all()
        return [project_to_domain(model) for model in models]

    def get_by_id(self, project_id: int) -> Project | None:
        model = self._session.get(ProjectORM, project_id)
        return None if model is None else project_to_domain(model)

    def get_by_id_for_update(self, project_id: int) -> Project | None:
        model = self._session.scalar(
            select(ProjectORM).where(ProjectORM.id == project_id).with_for_update()
        )
        return None if model is None else project_to_domain(model)

    def add(self, project: Project) -> Project:
        model = new_project_to_orm(project)
        self._session.add(model)
        try:
            self._session.flush()
        except IntegrityError as error:
            if (
                get_sqlstate(error) == UNIQUE_VIOLATION
                and get_constraint_name(error) in PROJECT_NAME_CONSTRAINTS
            ):
                raise exc.ProjectAlreadyExists(
                    f"Project with name '{project.name}' already exists"
                ) from error
            raise
        return project_to_domain(model)

    def save(self, project: Project) -> Project:
        if project.id is None:
            raise ValueError("Cannot save a project without an id")
        model = self._session.get(ProjectORM, project.id)
        if model is None:
            raise RuntimeError("Project disappeared before it could be saved")
        apply_project_to_orm(project, model)
        try:
            self._session.flush()
        except IntegrityError as error:
            if (
                get_sqlstate(error) == UNIQUE_VIOLATION
                and get_constraint_name(error) in PROJECT_NAME_CONSTRAINTS
            ):
                raise exc.ProjectAlreadyExists(
                    f"Project with name '{project.name}' already exists"
                ) from error
            raise
        return project_to_domain(model)

    def delete(self, project_id: int) -> None:
        model = self._session.get(ProjectORM, project_id)
        if model is None:
            raise RuntimeError("Project disappeared before it could be deleted")
        self._session.delete(model)
        try:
            self._session.flush()
        except IntegrityError as error:
            if (
                get_sqlstate(error) == FOREIGN_KEY_VIOLATION
                and get_constraint_name(error) == "fk_runs_project"
            ):
                raise exc.ProjectInUse(
                    f"Project with id {project_id} is used by existing runs and "
                    "cannot be deleted"
                ) from error
            raise
