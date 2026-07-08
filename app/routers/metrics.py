from fastapi import APIRouter, Depends

from app.database import get_db
from app.crud import metrics as metrics_crud
from app.schemas import metrics as metrics_schemas

router = APIRouter(prefix="/runs/{run_id}/metrics", tags=["metrics"])


@router.get("/", response_model=list[metrics_schemas.MetricResponse])
def get_metrics(run_id: int, db=Depends(get_db)):
    return metrics_crud.get_metrics(run_id, db)


@router.get("/{metric_id}", response_model=metrics_schemas.MetricResponse)
def get_metric(run_id: int, metric_id: int, db=Depends(get_db)):
    return metrics_crud.get_metric(run_id, metric_id, db)


@router.post("/", status_code=201, response_model=metrics_schemas.MetricResponse)
def create_metric(
    run_id: int,
    metric: metrics_schemas.MetricCreate,
    db=Depends(get_db),
):
    return metrics_crud.create_metric(run_id, metric, db)


@router.patch("/{metric_id}", response_model=metrics_schemas.MetricResponse)
def update_metric(
    run_id: int,
    metric_id: int,
    metric: metrics_schemas.MetricUpdate,
    db=Depends(get_db),
):
    return metrics_crud.update_metric(run_id, metric_id, metric, db)


@router.delete("/{metric_id}", status_code=204)
def delete_metric(run_id: int, metric_id: int, db=Depends(get_db)):
    return metrics_crud.delete_metric(run_id, metric_id, db)
