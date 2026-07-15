from dataclasses import dataclass

from app.domain.errors import InvalidProjectData
from app.domain.validation import optional_text, required_text


@dataclass(slots=True, kw_only=True)
class Project:
    name: str
    description: str | None = None
    id: int | None = None

    def __post_init__(self) -> None:
        self.rename(self.name)
        self.change_description(self.description)

    def rename(self, name: object) -> None:
        self.name = required_text(name, "Project name", InvalidProjectData)

    def change_description(self, description: object) -> None:
        self.description = optional_text(
            description,
            "Project description",
            InvalidProjectData,
        )
