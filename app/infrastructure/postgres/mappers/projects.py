from app.domain.projects import Project
from app.infrastructure.postgres.orm_models.projects import ProjectORM


def project_to_domain(project_orm: ProjectORM) -> Project:
    return Project(
        id=project_orm.id,
        name=project_orm.name,
        description=project_orm.description,
    )


def new_project_to_orm(project: Project) -> ProjectORM:
    if project.id is not None:
        raise ValueError("A new project must not already have an id")
    return ProjectORM(name=project.name, description=project.description)


def apply_project_to_orm(project: Project, project_orm: ProjectORM) -> None:
    if project.id is None or project.id != project_orm.id:
        raise ValueError("Domain and ORM project ids do not match")
    project_orm.name = project.name
    project_orm.description = project.description
