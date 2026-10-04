import unittest
from datetime import datetime, timezone

from app.application.exceptions import metric_directions as direction_errors
from app.application.exceptions import runs as run_errors
from app.application.use_cases.metrics import (
    CreateMetric,
    CreateMetricCommand,
)
from app.application.use_cases.parameters import (
    CreateParameter,
    CreateParameterCommand,
)
from app.application.use_cases.runs.lifecycle import (
    CompleteRun,
    IgnoreRun,
    IgnoreRunCommand,
    StartRun,
    UnignoreRun,
)
from app.application.use_cases.runs.ranking import CompareProjectRuns
from app.domain.metric_directions import MetricDirection
from app.domain.runs import Run, RunRankingItem, RunStatus


class _RunRepository:
    def __init__(self, run: Run):
        self.run = run
        self.saved = []

    def get_by_id(self, run_id: int) -> Run | None:
        return self.run if self.run.id == run_id else None

    def get_by_id_for_update(self, run_id: int) -> Run | None:
        return self.get_by_id(run_id)

    def save(self, run: Run) -> Run:
        self.saved.append(run)
        self.run = run
        return run


class _CollectionRepository:
    def __init__(self, *, exists: bool = False):
        self.exists = exists

    def exists_for_run(self, run_id: int) -> bool:
        return self.exists


class _DirectionRepository:
    def __init__(self, direction: MetricDirection | None):
        self.direction = direction

    def get_by_name(self, name: str) -> MetricDirection | None:
        if self.direction and self.direction.name == name:
            return self.direction
        return None


class _ProjectRepository:
    def __init__(self, exists: bool = True):
        self.exists = exists

    def get_by_id(self, project_id: int) -> object | None:
        return object() if self.exists else None


class _RankingRepository:
    def __init__(self, ranking: list[RunRankingItem]):
        self.ranking = ranking
        self.calls: list[tuple[int, str, bool]] = []

    def rank_project_runs(
        self,
        project_id: int,
        metric_name: str,
        *,
        maximize: bool,
    ) -> list[RunRankingItem]:
        self.calls.append((project_id, metric_name, maximize))
        return self.ranking


class _Uow:
    def __init__(self, run: Run):
        self.runs = _RunRepository(run)
        self.parameters = _CollectionRepository()
        self.metrics = _CollectionRepository()
        self.metric_directions = _DirectionRepository(None)
        self.projects = _ProjectRepository()
        self.commits = 0

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def commit(self) -> None:
        self.commits += 1


class _Clock:
    timestamp = datetime(2026, 1, 2, 3, 4, tzinfo=timezone.utc)

    def now(self) -> datetime:
        return self.timestamp


def _run(status: RunStatus = RunStatus.WAITING) -> Run:
    return Run(
        id=1,
        project_id=2,
        dataset_id=3,
        model_id=4,
        status=status,
    )


class LifecycleUseCaseTests(unittest.TestCase):
    def test_start_requires_at_least_one_parameter(self) -> None:
        uow = _Uow(_run())
        use_case = StartRun(lambda: uow, _Clock())

        with self.assertRaises(run_errors.RunStatusError):
            use_case.execute(1)

        self.assertEqual(uow.runs.run.status, RunStatus.WAITING)
        self.assertEqual(uow.commits, 0)

    def test_start_changes_waiting_run_to_running(self) -> None:
        uow = _Uow(_run())
        uow.parameters.exists = True
        use_case = StartRun(lambda: uow, _Clock())

        started = use_case.execute(1)

        self.assertEqual(started.status, RunStatus.RUNNING)
        self.assertEqual(started.start_time, _Clock.timestamp)
        self.assertEqual(uow.commits, 1)

    def test_parameters_are_locked_after_start(self) -> None:
        uow = _Uow(_run(RunStatus.RUNNING))
        use_case = CreateParameter(lambda: uow)

        with self.assertRaises(run_errors.RunStatusError):
            use_case.execute(
                CreateParameterCommand(
                    run_id=1,
                    name="learning_rate",
                    value="0.01",
                )
            )

        self.assertEqual(uow.commits, 0)

    def test_metrics_are_only_mutable_while_running(self) -> None:
        uow = _Uow(_run())
        uow.metric_directions.direction = MetricDirection(
            name="accuracy",
            maximize=True,
        )
        use_case = CreateMetric(lambda: uow)

        with self.assertRaises(run_errors.RunStatusError):
            use_case.execute(CreateMetricCommand(run_id=1, name="accuracy", value=0.9))

        self.assertEqual(uow.commits, 0)

    def test_completion_requires_at_least_one_metric(self) -> None:
        uow = _Uow(_run(RunStatus.RUNNING))
        use_case = CompleteRun(lambda: uow, _Clock())

        with self.assertRaises(run_errors.RunStatusError):
            use_case.execute(1)

        self.assertEqual(uow.runs.run.status, RunStatus.RUNNING)
        self.assertEqual(uow.commits, 0)

    def test_ignore_and_unignore_preserve_run_and_clear_reason(self) -> None:
        uow = _Uow(_run(RunStatus.COMPLETED))
        ignore = IgnoreRun(lambda: uow)
        unignore = UnignoreRun(lambda: uow)

        ignored = ignore.execute(IgnoreRunCommand(run_id=1, reason="bad seed"))
        self.assertTrue(ignored.is_ignored)
        self.assertEqual(ignored.ignore_reason, "bad seed")

        restored = unignore.execute(1)
        self.assertFalse(restored.is_ignored)
        self.assertIsNone(restored.ignore_reason)
        self.assertEqual(uow.commits, 2)


class RankingUseCaseTests(unittest.TestCase):
    def test_ranking_passes_direction_and_maximize_to_repository(self) -> None:
        result = RunRankingItem(
            run_id=1,
            project_id=2,
            dataset_id=3,
            model_id=4,
            status=RunStatus.COMPLETED,
            start_time=None,
            end_time=None,
            notes=None,
            metric_name="loss",
            metric_value=0.1,
            maximize=False,
        )
        uow = _Uow(_run())
        uow.metric_directions.direction = MetricDirection(
            name="loss",
            maximize=False,
        )
        uow.runs = _RankingRepository([result])

        ranked = CompareProjectRuns(lambda: uow).execute(2, "loss")

        self.assertEqual(ranked, [result])
        self.assertEqual(uow.runs.calls, [(2, "loss", False)])

    def test_ranking_normalizes_metric_name(self) -> None:
        uow = _Uow(_run())
        uow.metric_directions.direction = MetricDirection(
            name="loss",
            maximize=False,
        )
        uow.runs = _RankingRepository([])

        with self.assertRaises(run_errors.RunHasNoMetrics):
            CompareProjectRuns(lambda: uow).execute(2, "  loss  ")

        self.assertEqual(uow.runs.calls, [(2, "loss", False)])

    def test_ranking_rejects_project_without_matching_direction(self) -> None:
        uow = _Uow(_run())

        with self.assertRaises(direction_errors.MetricDirectionNotFound):
            CompareProjectRuns(lambda: uow).execute(2, "accuracy")


if __name__ == "__main__":
    unittest.main()
