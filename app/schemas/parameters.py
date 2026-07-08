from pydantic import BaseModel, Field


class ParameterCreate(BaseModel):
    name: str = Field(min_length=1)
    value: str = Field(min_length=1)
    value_type: str | None = None
    notes: str | None = None


class ParameterResponse(BaseModel):
    id: int
    run_id: int
    name: str
    value: str
    value_type: str | None = None
    notes: str | None = None


class ParameterUpdate(BaseModel):
    name: str | None = None
    value: str | None = None
    value_type: str | None = None
    notes: str | None = None
