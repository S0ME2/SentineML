from pydantic import BaseModel, Field


class DatasetCreate(BaseModel):
    name: str = Field(min_length=1)
    version: str = Field(min_length=1)
    description: str | None = None
    dataset_hash: str | None = None
    source: str | None = None
    metadata: str | None = None


class DatasetResponse(BaseModel):
    id: int
    name: str
    version: str
    description: str | None = None
    dataset_hash: str | None = None
    source: str | None = None
    metadata: str | None = None


class DatasetUpdate(BaseModel):
    name: str | None = None
    version: str | None = None
    description: str | None = None
    dataset_hash: str | None = None
    source: str | None = None
    metadata: str | None = None
