from pydantic import BaseModel, ConfigDict, Field


class ParameterCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    value: str = Field(min_length=1, max_length=255)
    value_type: str | None = Field(default=None, max_length=100)
    notes: str | None = None


class ParameterResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    run_id: int
    name: str
    value: str
    value_type: str | None = None
    notes: str | None = None


class ParameterUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    value: str | None = Field(default=None, min_length=1, max_length=255)
    value_type: str | None = Field(default=None, max_length=100)
    notes: str | None = None
