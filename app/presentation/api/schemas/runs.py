from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.domain.runs import RunStatus


class RunCreate(BaseModel):
    project_id: int
    model_id: int
    dataset_id: int
    notes: str | None = None


class RunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    model_id: int
    dataset_id: int
    status: RunStatus
    start_time: datetime | None = None
    end_time: datetime | None = None
    notes: str | None = None
    is_ignored: bool
    ignore_reason: str | None = None
    reason: str | None = None


class RunUpdate(BaseModel):
    dataset_id: int | None = None
    model_id: int | None = None
    notes: str | None = None
    reason: str | None = None


class ProjectRunRankingItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    run_id: int
    project_id: int
    dataset_id: int
    model_id: int
    status: RunStatus
    start_time: datetime | None = None
    end_time: datetime | None = None
    notes: str | None = None
    metric_name: str
    metric_value: float
    maximize: bool
