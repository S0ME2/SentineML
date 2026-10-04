from dataclasses import dataclass
from math import isfinite

from app.domain.errors import InvalidMetricData
from app.domain.validation import optional_text, required_text


@dataclass(slots=True, kw_only=True)
class Metric:
    run_id: int
    name: str
    value: float
    notes: str | None = None
    id: int | None = None

    def __post_init__(self) -> None:
        self.rename(self.name)
        self.change_value(self.value)
        self.change_notes(self.notes)

    def rename(self, name: object) -> None:
        self.name = required_text(
            name, "Metric name", InvalidMetricData, max_length=255
        )

    def change_value(self, value: object) -> None:
        if isinstance(value, bool) or not isinstance(value, int | float):
            raise InvalidMetricData("Metric value must be a number")
        try:
            numeric_value = float(value)
        except (OverflowError, ValueError) as error:
            raise InvalidMetricData("Metric value must be finite") from error
        if not isfinite(numeric_value):
            raise InvalidMetricData("Metric value must be finite")
        self.value = numeric_value

    def change_notes(self, notes: object) -> None:
        self.notes = optional_text(notes, "Metric notes", InvalidMetricData)
