from pydantic import BaseModel, Field


class ModelCreate(BaseModel):
    name: str = Field(min_length=1)
    version: str = Field(min_length=1)
    description: str | None = None
    model_type: str | None = None
    metadata: str | None = None


class ModelResponse(BaseModel):
    id: int
    name: str
    version: str
    description: str | None = None
    model_type: str | None = None
    metadata: str | None = None


class ModelUpdate(BaseModel):
    name: str | None = None
    version: str | None = None
    description: str | None = None
    model_type: str | None = None
    metadata: str | None = None
