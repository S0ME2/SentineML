from fastapi import HTTPException
from psycopg.errors import ForeignKeyViolation, UniqueViolation

PROJECT_COLUMNS = """
    id,
    name,
    description
"""


def _project_by_id(project_id, db):
    cursor = db.execute(
        f"""
        SELECT {PROJECT_COLUMNS}
        FROM projects
        WHERE id = %s;
        """,
        (project_id,),
    )

    return cursor.fetchone()


def _get_project_or_404(project_id, db):
    project = _project_by_id(project_id, db)

    if project is None:
        raise HTTPException(
            status_code=404,
            detail=f"Project with id {project_id} not found",
        )

    return project


def get_projects(db):
    cursor = db.execute(
        f"""
        SELECT {PROJECT_COLUMNS}
        FROM projects
        ORDER BY id;
        """
    )

    return cursor.fetchall()


def get_project(project_id, db):
    return _get_project_or_404(project_id, db)


def create_project(project, db):
    try:
        cursor = db.execute(
            f"""
            INSERT INTO projects (name, description)
            VALUES (%s, %s)
            RETURNING {PROJECT_COLUMNS};
            """,
            (project.name, project.description),
        )

        created_project = cursor.fetchone()
        db.commit()
        return created_project

    except UniqueViolation:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail=f"Project with name '{project.name}' already exists",
        )


def update_project(project_id, project_update, db):
    _get_project_or_404(project_id, db)

    update_fields = {
        "name": project_update.name,
        "description": project_update.description,
    }
    update_fields = {
        column: value for column, value in update_fields.items() if value is not None
    }

    if not update_fields:
        raise HTTPException(
            status_code=400,
            detail="No fields to update",
        )

    assignments = ", ".join(f"{column} = %s" for column in update_fields)
    values = tuple(update_fields.values())

    try:
        cursor = db.execute(
            f"""
            UPDATE projects
            SET {assignments}
            WHERE id = %s
            RETURNING {PROJECT_COLUMNS};
            """,
            values + (project_id,),
        )

        updated_project = cursor.fetchone()
        db.commit()
        return updated_project

    except UniqueViolation:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail=f"Project with name '{project_update.name}' already exists",
        )


def delete_project(project_id, db):
    _get_project_or_404(project_id, db)

    try:
        db.execute(
            """
            DELETE FROM projects
            WHERE id = %s;
            """,
            (project_id,),
        )
        db.commit()

    except ForeignKeyViolation:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail=f"Project with id {project_id} is used by existing runs and cannot be deleted",
        )
