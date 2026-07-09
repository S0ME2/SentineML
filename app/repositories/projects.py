PROJECT_COLUMNS = """
    id,
    name,
    description
"""


def _project_by_id_for_update(project_id, db):
    cursor = db.execute(
        f"""
        SELECT {PROJECT_COLUMNS}
        FROM projects
        WHERE id = %s
        FOR UPDATE;
        """,
        (project_id,),
    )

    return cursor.fetchone()


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
    cursor = db.execute(
        f"""
        SELECT {PROJECT_COLUMNS}
        FROM projects
        WHERE id = %s;
        """,
        (project_id,),
    )

    return cursor.fetchone()


def create_project(project, db):
    cursor = db.execute(
        f"""
            INSERT INTO projects (name, description)
            VALUES (%s, %s)
            RETURNING {PROJECT_COLUMNS};
            """,
        (project.name, project.description),
    )

    return cursor.fetchone()


def update_project(project_id, update_fields, db):
    assignments = ", ".join(f"{column} = %s" for column in update_fields)
    values = tuple(update_fields.values())

    cursor = db.execute(
        f"""
        UPDATE projects
        SET {assignments}
        WHERE id = %s
        RETURNING {PROJECT_COLUMNS};
        """,
        values + (project_id,),
    )

    return cursor.fetchone()


def delete_project(project_id, db):
    db.execute(
        """
        DELETE FROM projects
        WHERE id = %s;
        """,
        (project_id,),
    )
