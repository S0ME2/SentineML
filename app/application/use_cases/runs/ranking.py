from app.application.exceptions import metric_directions as direction_exc
from app.application.exceptions import projects as project_exc
from app.application.exceptions import runs as exc
from app.application.ports.unit_of_work import UnitOfWorkFactory
from app.domain.runs import RunRankingItem


class CompareProjectRuns:
    def __init__(self, uow_factory: UnitOfWorkFactory):
        self._uow_factory = uow_factory

    def execute(self, project_id: int, metric_name: str) -> list[RunRankingItem]:
        with self._uow_factory() as uow:
            if uow.projects.get_by_id(project_id) is None:
                raise project_exc.ProjectNotFound(
                    f"Project with id {project_id} not found"
                )

            direction = uow.metric_directions.get_by_name(metric_name)
            if direction is None:
                raise direction_exc.MetricDirectionNotFound(
                    f"Metric direction '{metric_name}' not found"
                )

            ranked_runs = uow.runs.rank_project_runs(
                project_id,
                direction.name,
                maximize=direction.maximize,
            )

            if not ranked_runs:
                raise exc.RunHasNoMetrics(
                    f"Project with id {project_id} has no completed, non-ignored "
                    f"runs with metric '{metric_name}'"
                )

            return ranked_runs


class GetProjectBestRun:
    def __init__(self, compare_runs: CompareProjectRuns):
        self._compare_runs = compare_runs

    def execute(self, project_id: int, metric_name: str) -> RunRankingItem:
        return self._compare_runs.execute(project_id, metric_name)[0]
