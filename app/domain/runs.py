from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from app.domain.errors import InvalidRunData, InvalidRunState
from app.domain.validation import optional_text, required_text


class RunStatus(StrEnum):
    WAITING = "waiting"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass(slots=True, kw_only=True)
class Run:
    project_id: int
    dataset_id: int
    model_id: int
    id: int | None = None
    status: RunStatus = RunStatus.WAITING
    start_time: datetime | None = None
    end_time: datetime | None = None
    notes: str | None = None
    is_ignored: bool = False
    ignore_reason: str | None = None
    reason: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.status, RunStatus):
            try:
                self.status = RunStatus(self.status)
            except (TypeError, ValueError) as error:
                raise InvalidRunData(f"Unknown run status: {self.status}") from error

        self.change_notes(self.notes)
        self.ignore_reason = optional_text(
            self.ignore_reason,
            "Run ignore reason",
            InvalidRunData,
        )
        self.reason = optional_text(self.reason, "Run reason", InvalidRunData)

    def _require_status(self, allowed: set[RunStatus], action: str) -> None:
        if self.status not in allowed:
            allowed_values = ", ".join(sorted(status.value for status in allowed))
            raise InvalidRunState(
                f"Run with id {self.id} cannot be {action} while its status is "
                f"'{self.status.value}'. Allowed status: {allowed_values}"
            )

    def change_dataset(self, dataset_id: int) -> None:
        self._require_status({RunStatus.WAITING}, "assigned a different dataset")
        self.dataset_id = dataset_id

    def change_model(self, model_id: int) -> None:
        self._require_status({RunStatus.WAITING}, "assigned a different model")
        self.model_id = model_id

    def change_notes(self, notes: object) -> None:
        self.notes = optional_text(notes, "Run notes", InvalidRunData)

    def update_reason(self, reason: object) -> None:
        self._require_status(
            {RunStatus.FAILED, RunStatus.CANCELLED},
            "given a new reason",
        )
        self.reason = optional_text(reason, "Run reason", InvalidRunData)

    def ensure_parameters_can_change(self) -> None:
        self._require_status({RunStatus.WAITING}, "given modified parameters")

    def ensure_metrics_can_change(self) -> None:
        self._require_status({RunStatus.RUNNING}, "given modified metrics")

    def ensure_can_be_deleted(self) -> None:
        self._require_status({RunStatus.WAITING}, "deleted")

    def ensure_can_start(self) -> None:
        self._require_status({RunStatus.WAITING}, "started")

    def ensure_can_complete(self) -> None:
        self._require_status({RunStatus.RUNNING}, "completed")

    def start(self, started_at: datetime) -> None:
        self.ensure_can_start()
        self.status = RunStatus.RUNNING
        self.start_time = started_at
        self.end_time = None

    def complete(self, completed_at: datetime) -> None:
        self.ensure_can_complete()
        self.status = RunStatus.COMPLETED
        self.end_time = completed_at

    def fail(self, reason: object, failed_at: datetime) -> None:
        self._require_status({RunStatus.RUNNING}, "failed")
        self.reason = required_text(reason, "Run failure reason", InvalidRunData)
        self.status = RunStatus.FAILED
        self.end_time = failed_at

    def cancel(self, reason: object, cancelled_at: datetime) -> None:
        self._require_status(
            {RunStatus.WAITING, RunStatus.RUNNING},
            "cancelled",
        )
        self.reason = optional_text(reason, "Run cancellation reason", InvalidRunData)
        self.status = RunStatus.CANCELLED
        self.end_time = cancelled_at

    def ignore(self, reason: object) -> None:
        self.ignore_reason = required_text(
            reason,
            "Run ignore reason",
            InvalidRunData,
        )
        self.is_ignored = True

    def unignore(self) -> None:
        self.is_ignored = False
        self.ignore_reason = None


@dataclass(frozen=True, slots=True, kw_only=True)
class RunRankingItem:
    run_id: int
    project_id: int
    dataset_id: int
    model_id: int
    status: RunStatus
    start_time: datetime | None
    end_time: datetime | None
    notes: str | None
    metric_name: str
    metric_value: float
    maximize: bool
