from psycopg.errors import ForeignKeyViolation, UniqueViolation

from app.exceptions import projects as exc
from app.repositories import projects as projects_crud
from app.services.common import build_update_fields


def _get_project_for_update(project_id, db):
    project = projects_crud._project_by_id_for_update(project_id, db)

    if project is None:
        raise exc.ProjectNotFound(f"Project with id {project_id} not found")

    return project


def get_projects(db):
    return projects_crud.get_projects(db)


def get_project(project_id, db):
    project = projects_crud.get_project(project_id, db)

    if project is None:
        raise exc.ProjectNotFound(f"Project with id {project_id} not found")

    return project


def create_project(project, db):
    try:
        created_project = projects_crud.create_project(project, db)

        db.commit()
        return created_project

    except UniqueViolation:
        db.rollback()
        raise exc.ProjectAlreadyExists(
            f"Project with name '{project.name}' already exists"
        )

    except Exception:
        db.rollback()
        raise


def update_project(project_id, project_update, db):
    try:
        _get_project_for_update(project_id, db)

        update_fields = build_update_fields(
            {
                "name": project_update.name,
                "description": project_update.description,
            }
        )

        if not update_fields:
            raise exc.EmptyProjectUpdate("No fields to update")

        updated_project = projects_crud.update_project(project_id, update_fields, db)

        db.commit()
        return updated_project

    except UniqueViolation:
        db.rollback()
        raise exc.ProjectAlreadyExists(
            f"Project with name '{project_update.name}' already exists"
        )

    except Exception:
        db.rollback()
        raise


def delete_project(project_id, db):
    try:
        _get_project_for_update(project_id, db)

        projects_crud.delete_project(project_id, db)
        db.commit()

    except ForeignKeyViolation:
        db.rollback()
        raise exc.ProjectInUse(
            f"Project with id {project_id} is used by existing runs "
            "and cannot be deleted"
        )

    except Exception:
        db.rollback()
        raise
