from dataclasses import dataclass

from app.domain.errors import InvalidDatasetData
from app.domain.validation import optional_text, required_text


@dataclass(slots=True, kw_only=True)
class Dataset:
    name: str
    version: str
    description: str | None = None
    dataset_hash: str | None = None
    source: str | None = None
    metadata: str | None = None
    id: int | None = None

    def __post_init__(self) -> None:
        self.rename(self.name)
        self.change_version(self.version)
        self.change_description(self.description)
        self.change_dataset_hash(self.dataset_hash)
        self.change_source(self.source)
        self.change_metadata(self.metadata)

    def rename(self, name: object) -> None:
        self.name = required_text(name, "Dataset name", InvalidDatasetData)

    def change_version(self, version: object) -> None:
        self.version = required_text(version, "Dataset version", InvalidDatasetData)

    def change_description(self, description: object) -> None:
        self.description = optional_text(
            description,
            "Dataset description",
            InvalidDatasetData,
        )

    def change_dataset_hash(self, dataset_hash: object) -> None:
        self.dataset_hash = optional_text(
            dataset_hash,
            "Dataset hash",
            InvalidDatasetData,
        )

    def change_source(self, source: object) -> None:
        self.source = optional_text(source, "Dataset source", InvalidDatasetData)

    def change_metadata(self, metadata: object) -> None:
        self.metadata = optional_text(
            metadata,
            "Dataset metadata",
            InvalidDatasetData,
        )
