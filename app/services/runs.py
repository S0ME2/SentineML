from psycopg.errors import ForeignKeyViolation

from app.database import create_connection
from app.exceptions import (
    base,
)
from app.exceptions import (
    runs as exc,
)
from app.repositories import runs as runs_crud
from app.services import (
    datasets as datasets_services,
)
from app.services import (
    metric_directions as metric_directions_services,
)
from app.services import (
    metrics as metrics_services,
)
from app.services import (
    models as models_services,
)
from app.services import (
    parameters as parameters_services,
)
from app.services import (
    projects as projects_services,
)
from app.services.common import build_update_fields, require_status


def _run_status_error(run_id, status, action, requirement):
    return exc.RunStatusError(
        f"Run with id {run_id} cannot be {action} because its status "
        f"is '{status}'. {requirement}"
    )


def _validate_run_references(project_id, dataset_id, model_id, db):
    projects_services._get_project_for_update(project_id, db)
    datasets_services._get_dataset_for_update(dataset_id, db)
    models_services._get_model_for_update(model_id, db)


def _get_run_for_update(run_id, db):
    run = runs_crud._run_by_id_for_update(run_id, db)

    if run is None:
        raise exc.RunNotFound(f"Run with id {run_id} not found")

    return run


def get_runs():
    db = create_connection()

    try:
        return runs_crud.get_runs(db)

    except Exception:
        raise

    finally:
        db.close()


def get_run(run_id):
    db = create_connection()

    try:
        run = runs_crud.get_run(run_id, db)

        if run is None:
            raise exc.RunNotFound(f"Run with id {run_id} not found")

        return run

    except Exception:
        raise

    finally:
        db.close()


def create_run(run):
    db = create_connection()

    try:
        _validate_run_references(run.project_id, run.dataset_id, run.model_id, db)

        created_run = runs_crud.create_run(run, db)

        db.commit()
        return created_run

    except ForeignKeyViolation:
        db.rollback()
        raise base.NotFoundError("Project, dataset or model not found")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


def update_run(run_id, run_update):
    db = create_connection()

    try:
        run = _get_run_for_update(run_id, db)

        update_fields = {}

        if (dataset_id := run_update.dataset_id) is not None:
            require_status(
                run["status"],
                {"waiting"},
                exc.RunStatusError(
                    "Dataset can only be changed while the run is waiting"
                ),
            )
            datasets_services._get_dataset_for_update(dataset_id, db)
            update_fields["dataset_id"] = dataset_id

        if (model_id := run_update.model_id) is not None:
            require_status(
                run["status"],
                {"waiting"},
                exc.RunStatusError(
                    "Model can only be changed while the run is waiting"
                ),
            )
            models_services._get_model_for_update(model_id, db)
            update_fields["model_id"] = model_id

        if run_update.notes is not None:
            update_fields["notes"] = run_update.notes

        if run_update.reason is not None:
            require_status(
                run["status"],
                {"failed", "cancelled"},
                exc.RunStatusError(
                    "Reason can only be updated for failed or cancelled runs"
                ),
            )
            update_fields["reason"] = run_update.reason

        update_fields = build_update_fields(update_fields)

        if not update_fields:
            raise exc.EmptyRunUpdate("No fields to update")

        updated_run = runs_crud.update_run(run_id, update_fields, db)

        db.commit()
        return updated_run

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


def delete_run(run_id):
    db = create_connection()

    try:
        run = _get_run_for_update(run_id, db)

        require_status(
            run["status"],
            {"waiting"},
            _run_status_error(
                run_id,
                run["status"],
                "deleted",
                "Only waiting runs can be deleted. Use ignore instead.",
            ),
        )

        runs_crud.delete_run(run_id, db)
        db.commit()

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


def start_run(run_id, db):
    db = create_connection()

    try:
        run = _get_run_for_update(run_id, db)

        require_status(
            run["status"],
            {"waiting"},
            _run_status_error(
                run_id,
                run["status"],
                "started",
                "Only waiting runs can be started.",
            ),
        )

        if not parameters_services._get_parameters_for_update(run_id, db):
            raise exc.RunStatusError(
                f"Run with id {run_id} cannot be started because it has no parameters."
            )

        started_run = runs_crud.start_run(run_id, db)
        db.commit()
        return started_run

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


def cancel_run(run_id, reason):
    db = create_connection()

    try:
        run = _get_run_for_update(run_id, db)

        require_status(
            run["status"],
            {"waiting", "running"},
            exc.RunStatusError(
                f"Run with id {run_id} cannot be canceled because it is in "
                f"'{run['status']}' status"
            ),
        )

        canceled_run = runs_crud.cancel_run(run_id, reason, db)

        db.commit()
        return canceled_run

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


def fail_run(run_id, reason):
    db = create_connection()

    try:
        run = _get_run_for_update(run_id, db)

        require_status(
            run["status"],
            {"running"},
            exc.RunStatusError(
                f"Run with id {run_id} cannot be failed because it is in "
                f"'{run['status']}' status"
            ),
        )

        failed_run = runs_crud.fail_run(run_id, reason, db)

        db.commit()
        return failed_run

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


def ignore_run(run_id, ignore_reason):
    db = create_connection()

    try:
        _get_run_for_update(run_id, db)

        ignored_run = runs_crud.ignore_run(run_id, ignore_reason, db)

        db.commit()
        return ignored_run

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


def unignore_run(run_id):
    db = create_connection()

    try:
        _get_run_for_update(run_id, db)

        ignored_run = runs_crud.unignore_run(run_id, db)

        db.commit()
        return ignored_run

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


def complete_run(run_id):
    db = create_connection()

    try:
        run = _get_run_for_update(run_id, db)

        require_status(
            run["status"],
            {"running"},
            exc.RunStatusError(
                f"Run with id {run_id} cannot be completed because it is in "
                f"'{run['status']}' status"
            ),
        )

        if not metrics_services._get_metrics_for_update(run_id, db):
            raise exc.RunStatusError(
                f"Run with id {run_id} cannot be completed because it has no metrics"
            )

        completed_run = runs_crud.complete_run(run_id, db)

        db.commit()
        return completed_run

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


def compare_project_runs(project_id, metric_name):
    db = create_connection()

    try:
        projects_services.get_project(project_id, db)

        metric_direction = metric_directions_services.get_metric_direction(
            metric_name, db
        )
        sort_direction = "DESC" if metric_direction["maximize"] else "ASC"

        ranked_runs = runs_crud.compare_project_runs(
            project_id,
            metric_name,
            sort_direction,
            db,
        )

        if not ranked_runs:
            raise exc.RunHasNoMetrics(
                f"Project with id {project_id} has no completed, non-ignored runs "
                f"with metric '{metric_name}'"
            )

        return ranked_runs

    except Exception:
        raise

    finally:
        db.close()


def get_project_best_run(project_id, metric_name):
    ranked_runs = compare_project_runs(project_id, metric_name)
    return ranked_runs[0]
