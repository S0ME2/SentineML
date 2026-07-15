from collections.abc import Mapping
from dataclasses import dataclass

from app.application.exceptions import projects as exc
from app.application.ports.caches import ProjectCache
from app.application.ports.unit_of_work import UnitOfWorkFactory
from app.domain.errors import InvalidProjectData as DomainInvalidProjectData
from app.domain.projects import Project


@dataclass(frozen=True, slots=True, kw_only=True)
class CreateProjectCommand:
    name: str
    description: str | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class UpdateProjectCommand:
    project_id: int
    fields: Mapping[str, object]


class ListProjects:
    def __init__(self, uow_factory: UnitOfWorkFactory):
        self._uow_factory = uow_factory

    def execute(self) -> list[Project]:
        with self._uow_factory() as uow:
            return uow.projects.list_all()


class GetProject:
    def __init__(self, uow_factory: UnitOfWorkFactory, cache: ProjectCache):
        self._uow_factory = uow_factory
        self._cache = cache

    def execute(self, project_id: int) -> Project:
        cached_project = self._cache.get(project_id)
        if cached_project is not None:
            return cached_project

        with self._uow_factory() as uow:
            project = uow.projects.get_by_id(project_id)
            if project is None:
                raise exc.ProjectNotFound(f"Project with id {project_id} not found")

        self._cache.put(project)
        return project


class CreateProject:
    def __init__(self, uow_factory: UnitOfWorkFactory, cache: ProjectCache):
        self._uow_factory = uow_factory
        self._cache = cache

    def execute(self, command: CreateProjectCommand) -> Project:
        try:
            project = Project(name=command.name, description=command.description)
        except DomainInvalidProjectData as error:
            raise exc.InvalidProjectData(str(error)) from error

        with self._uow_factory() as uow:
            created_project = uow.projects.add(project)
            uow.commit()

        self._cache.put(created_project)
        return created_project


class UpdateProject:
    ALLOWED_FIELDS = {"name", "description"}

    def __init__(self, uow_factory: UnitOfWorkFactory, cache: ProjectCache):
        self._uow_factory = uow_factory
        self._cache = cache

    def execute(self, command: UpdateProjectCommand) -> Project:
        fields = dict(command.fields)
        if not fields:
            raise exc.EmptyProjectUpdate("No fields to update")

        unknown_fields = set(fields) - self.ALLOWED_FIELDS
        if unknown_fields:
            raise exc.InvalidProjectData(
                f"Unsupported project fields: {sorted(unknown_fields)}"
            )

        with self._uow_factory() as uow:
            project = uow.projects.get_by_id_for_update(command.project_id)
            if project is None:
                raise exc.ProjectNotFound(
                    f"Project with id {command.project_id} not found"
                )

            try:
                if "name" in fields:
                    project.rename(fields["name"])
                if "description" in fields:
                    project.change_description(fields["description"])
            except DomainInvalidProjectData as error:
                raise exc.InvalidProjectData(str(error)) from error

            updated_project = uow.projects.save(project)
            uow.commit()

        self._cache.invalidate(command.project_id)
        return updated_project


class DeleteProject:
    def __init__(self, uow_factory: UnitOfWorkFactory, cache: ProjectCache):
        self._uow_factory = uow_factory
        self._cache = cache

    def execute(self, project_id: int) -> None:
        with self._uow_factory() as uow:
            project = uow.projects.get_by_id_for_update(project_id)
            if project is None:
                raise exc.ProjectNotFound(f"Project with id {project_id} not found")

            uow.projects.delete(project_id)
            uow.commit()

        self._cache.invalidate(project_id)
