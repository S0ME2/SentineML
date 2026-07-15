from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.application.exceptions import datasets as dataset_exc
from app.application.exceptions import models as model_exc
from app.application.exceptions import projects as project_exc
from app.application.exceptions import runs as exc
from app.application.ports.repositories import RunRepository
from app.domain.runs import Run, RunRankingItem, RunStatus
from app.infrastructure.postgres.integrity import (
    FOREIGN_KEY_VIOLATION,
    get_constraint_name,
    get_sqlstate,
)
from app.infrastructure.postgres.mappers.runs import (
    apply_run_to_orm,
    new_run_to_orm,
    run_to_domain,
)
from app.infrastructure.postgres.orm_models.metric_directions import (
    MetricDirectionORM,
)
from app.infrastructure.postgres.orm_models.metrics import MetricORM
from app.infrastructure.postgres.orm_models.runs import RunORM


class SQLAlchemyRunRepository(RunRepository):
    def __init__(self, session: Session):
        self._session = session

    def list_all(self) -> list[Run]:
        models = self._session.scalars(select(RunORM).order_by(RunORM.id)).all()
        return [run_to_domain(model) for model in models]

    def get_by_id(self, run_id: int) -> Run | None:
        model = self._session.get(RunORM, run_id)
        return None if model is None else run_to_domain(model)

    def get_by_id_for_update(self, run_id: int) -> Run | None:
        model = self._session.scalar(
            select(RunORM).where(RunORM.id == run_id).with_for_update()
        )
        return None if model is None else run_to_domain(model)

    def add(self, run: Run) -> Run:
        model = new_run_to_orm(run)
        self._session.add(model)
        try:
            self._session.flush()
        except IntegrityError as error:
            self._translate_reference_error(error, run)
            raise
        return run_to_domain(model)

    def save(self, run: Run) -> Run:
        if run.id is None:
            raise ValueError("Cannot save a run without an id")
        model = self._session.get(RunORM, run.id)
        if model is None:
            raise RuntimeError("Run disappeared before it could be saved")
        apply_run_to_orm(run, model)
        try:
            self._session.flush()
        except IntegrityError as error:
            self._translate_reference_error(error, run)
            raise
        return run_to_domain(model)

    def delete(self, run_id: int) -> None:
        model = self._session.get(RunORM, run_id)
        if model is None:
            raise RuntimeError("Run disappeared before it could be deleted")
        self._session.delete(model)
        try:
            self._session.flush()
        except IntegrityError as error:
            if (
                get_sqlstate(error) == FOREIGN_KEY_VIOLATION
                and get_constraint_name(error) == "fk_metrics_run"
            ):
                raise exc.RunInUse(
                    f"Run with id {run_id} has metrics and cannot be deleted"
                ) from error
            raise

    def rank_project_runs(
        self,
        project_id: int,
        metric_name: str,
        *,
        maximize: bool,
    ) -> list[RunRankingItem]:
        runs = RunORM.__table__
        metrics = MetricORM.__table__
        directions = MetricDirectionORM.__table__

        order_expression = metrics.c.value.desc() if maximize else metrics.c.value.asc()

        statement = (
            select(
                runs.c.id.label("run_id"),
                runs.c.project_id,
                runs.c.dataset_id,
                runs.c.model_id,
                runs.c.status,
                runs.c.start_time,
                runs.c.end_time,
                runs.c.notes,
                metrics.c.name.label("metric_name"),
                metrics.c.value.label("metric_value"),
                directions.c.maximize,
            )
            .select_from(
                runs.join(metrics, metrics.c.run_id == runs.c.id).join(
                    directions,
                    directions.c.name == metrics.c.name,
                )
            )
            .where(
                runs.c.project_id == project_id,
                runs.c.status == RunStatus.COMPLETED,
                runs.c.is_ignored.is_(False),
                metrics.c.name == metric_name,
            )
            .order_by(order_expression, runs.c.id.asc())
        )

        rows = self._session.execute(statement).mappings().all()
        return [
            RunRankingItem(
                run_id=row["run_id"],
                project_id=row["project_id"],
                dataset_id=row["dataset_id"],
                model_id=row["model_id"],
                status=row["status"],
                start_time=row["start_time"],
                end_time=row["end_time"],
                notes=row["notes"],
                metric_name=row["metric_name"],
                metric_value=row["metric_value"],
                maximize=row["maximize"],
            )
            for row in rows
        ]

    @staticmethod
    def _translate_reference_error(error: IntegrityError, run: Run) -> None:
        if get_sqlstate(error) != FOREIGN_KEY_VIOLATION:
            return

        constraint = get_constraint_name(error)
        if constraint == "fk_runs_project":
            raise project_exc.ProjectNotFound(
                f"Project with id {run.project_id} not found"
            ) from error
        if constraint == "fk_runs_dataset":
            raise dataset_exc.DatasetNotFound(
                f"Dataset with id {run.dataset_id} not found"
            ) from error
        if constraint == "fk_runs_model":
            raise model_exc.ModelNotFound(
                f"Model with id {run.model_id} not found"
            ) from error
