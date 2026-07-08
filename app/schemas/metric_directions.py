from pydantic import BaseModel, Field


class MetricDirectionCreate(BaseModel):
    name: str = Field(min_length=1)
    maximize: bool


class MetricDirectionResponse(BaseModel):
    name: str
    maximize: bool


class MetricDirectionUpdate(BaseModel):
    maximize: bool
