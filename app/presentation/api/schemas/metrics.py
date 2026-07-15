from pydantic import BaseModel, ConfigDict, Field


class MetricCreate(BaseModel):
    name: str = Field(min_length=1)
    value: float
    notes: str | None = None


class MetricResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    run_id: int
    name: str
    value: float
    notes: str | None = None


class MetricUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1)
    value: float | None = None
    notes: str | None = None
