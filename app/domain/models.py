from dataclasses import dataclass

from app.domain.errors import InvalidModelData
from app.domain.validation import optional_text, required_text


@dataclass(slots=True, kw_only=True)
class Model:
    name: str
    version: str
    description: str | None = None
    model_type: str | None = None
    metadata: str | None = None
    id: int | None = None

    def __post_init__(self) -> None:
        self.rename(self.name)
        self.change_version(self.version)
        self.change_description(self.description)
        self.change_model_type(self.model_type)
        self.change_metadata(self.metadata)

    def rename(self, name: object) -> None:
        self.name = required_text(name, "Model name", InvalidModelData)

    def change_version(self, version: object) -> None:
        self.version = required_text(version, "Model version", InvalidModelData)

    def change_description(self, description: object) -> None:
        self.description = optional_text(
            description,
            "Model description",
            InvalidModelData,
        )

    def change_model_type(self, model_type: object) -> None:
        self.model_type = optional_text(
            model_type,
            "Model type",
            InvalidModelData,
        )

    def change_metadata(self, metadata: object) -> None:
        self.metadata = optional_text(
            metadata,
            "Model metadata",
            InvalidModelData,
        )
