from pydantic import BaseModel, ConfigDict, Field


class MetricDirectionCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    maximize: bool


class MetricDirectionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    maximize: bool


class MetricDirectionUpdate(BaseModel):
    maximize: bool
