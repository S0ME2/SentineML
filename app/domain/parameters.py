from dataclasses import dataclass

from app.domain.errors import InvalidParameterData
from app.domain.validation import optional_text, required_text


@dataclass(slots=True, kw_only=True)
class Parameter:
    run_id: int
    name: str
    value: str
    value_type: str | None = None
    notes: str | None = None
    id: int | None = None

    def __post_init__(self) -> None:
        self.rename(self.name)
        self.change_value(self.value)
        self.change_value_type(self.value_type)
        self.change_notes(self.notes)

    def rename(self, name: object) -> None:
        self.name = required_text(
            name, "Parameter name", InvalidParameterData, max_length=255
        )

    def change_value(self, value: object) -> None:
        self.value = required_text(
            value, "Parameter value", InvalidParameterData, max_length=255
        )

    def change_value_type(self, value_type: object) -> None:
        self.value_type = optional_text(
            value_type,
            "Parameter value type",
            InvalidParameterData,
            max_length=100,
        )

    def change_notes(self, notes: object) -> None:
        self.notes = optional_text(notes, "Parameter notes", InvalidParameterData)
