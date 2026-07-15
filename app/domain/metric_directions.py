from dataclasses import dataclass

from app.domain.errors import InvalidMetricDirectionData
from app.domain.validation import required_text


@dataclass(slots=True, kw_only=True)
class MetricDirection:
    name: str
    maximize: bool

    def __post_init__(self) -> None:
        self.name = required_text(
            self.name,
            "Metric direction name",
            InvalidMetricDirectionData,
        )
        self.change_maximize(self.maximize)

    def change_maximize(self, maximize: object) -> None:
        if not isinstance(maximize, bool):
            raise InvalidMetricDirectionData(
                "Metric direction maximize must be a boolean"
            )
        self.maximize = maximize
