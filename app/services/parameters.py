from psycopg.errors import UniqueViolation

from app.exceptions import parameters as exc
from app.exceptions import runs as runs_exc
from app.repositories import parameters as parameters_crud
from app.services import runs as runs_services
from app.services.common import build_update_fields, require_found, require_status


def _get_parameters_for_update(run_id, db):
    return parameters_crud._get_parameters_for_update(run_id, db)


def get_parameters(run_id, db):
    runs_services.get_run(run_id, db)
    return parameters_crud.get_parameters(run_id, db)


def get_parameter(run_id, parameter_id, db):
    runs_services.get_run(run_id, db)
    return require_found(
        parameters_crud.get_parameter(run_id, parameter_id, db),
        exc.ParameterNotFound(
            f"Parameter with id {parameter_id} not found for run with id {run_id}"
        ),
    )


def create_parameter(run_id, parameter, db):
    try:
        run = runs_services._get_run_for_update(run_id, db)

        require_status(
            run["status"],
            {"waiting"},
            runs_exc.RunStatusError(f"Run with id {run_id} is not in 'waiting' status"),
        )

        created_parameter = parameters_crud.create_parameter(run_id, parameter, db)

        db.commit()
        return created_parameter

    except UniqueViolation:
        db.rollback()
        raise exc.ParameterAlreadyExists(
            f"Parameter with name '{parameter.name}' already exists "
            f"for run with id {run_id}"
        )

    except Exception:
        db.rollback()
        raise


def update_parameter(run_id, parameter_id, parameter_update, db):
    try:
        run = runs_services._get_run_for_update(run_id, db)

        require_status(
            run["status"],
            {"waiting"},
            runs_exc.RunStatusError(f"Run with id {run_id} is not in 'waiting' status"),
        )

        update_fields = build_update_fields(
            {
                "name": parameter_update.name,
                "value": parameter_update.value,
                "value_type": parameter_update.value_type,
                "notes": parameter_update.notes,
            }
        )

        if not update_fields:
            raise exc.EmptyParameterUpdate(
                "No fields to update for parameter with id "
                f"{parameter_id} and run with id {run_id}"
            )

        updated_parameter = parameters_crud.update_parameter(
            run_id, parameter_id, update_fields, db
        )

        require_found(
            updated_parameter,
            exc.ParameterNotFound(
                f"Parameter with id {parameter_id} not found for run with id {run_id}"
            ),
        )

        db.commit()
        return updated_parameter

    except UniqueViolation:
        db.rollback()
        raise exc.ParameterAlreadyExists(
            f"Parameter with name '{parameter_update.name}' already exists "
            f"for run with id {run_id}"
        )

    except Exception:
        db.rollback()
        raise


def delete_parameter(run_id, parameter_id, db):
    try:
        run = runs_services._get_run_for_update(run_id, db)

        require_status(
            run["status"],
            {"waiting"},
            runs_exc.RunStatusError(f"Run with id {run_id} is not in 'waiting' status"),
        )

        deleted_parameter = parameters_crud.delete_parameter(run_id, parameter_id, db)

        require_found(
            deleted_parameter,
            exc.ParameterNotFound(
                f"Parameter with id {parameter_id} not found for run with id {run_id}"
            ),
        )

        db.commit()
        return deleted_parameter

    except Exception:
        db.rollback()
        raise
