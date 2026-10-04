from pydantic import BaseModel, ConfigDict, Field


class ModelCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    version: str = Field(min_length=1, max_length=255)
    description: str | None = None
    model_type: str | None = Field(default=None, max_length=255)
    metadata: str | None = None


class ModelResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    version: str
    description: str | None = None
    model_type: str | None = None
    metadata: str | None = None


class ModelUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    version: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    model_type: str | None = Field(default=None, max_length=255)
    metadata: str | None = None
