from pydantic import BaseModel, ConfigDict, Field, FiniteFloat


class MetricCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    value: FiniteFloat
    notes: str | None = None


class MetricResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    run_id: int
    name: str
    value: FiniteFloat
    notes: str | None = None


class MetricUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    value: FiniteFloat | None = None
    notes: str | None = None
