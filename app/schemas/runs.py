from datetime import datetime
from typing import Literal

from pydantic import BaseModel

RunStatus = Literal["waiting", "running", "completed", "failed", "cancelled"]


class RunCreate(BaseModel):
    project_id: int
    model_id: int
    dataset_id: int
    notes: str | None = None


class RunResponse(BaseModel):
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
