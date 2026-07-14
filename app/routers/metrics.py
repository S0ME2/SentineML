import fastapi

from app.exceptions.base import AppError
from app.routers.error_handlers import raise_http_error
from app.schemas import metrics as metrics_schemas
from app.services import metrics as metrics_services

router = fastapi.APIRouter(prefix="/runs/{run_id}/metrics", tags=["metrics"])


@router.get("/", response_model=list[metrics_schemas.MetricResponse])
def get_metrics(run_id: int):
    try:
        return metrics_services.get_metrics(run_id)

    except AppError as error:
        raise_http_error(error)


@router.get("/{metric_id}", response_model=metrics_schemas.MetricResponse)
def get_metric(run_id: int, metric_id: int):
    try:
        return metrics_services.get_metric(run_id, metric_id)

    except AppError as error:
        raise_http_error(error)


@router.post("/", status_code=201, response_model=metrics_schemas.MetricResponse)
def create_metric(
    run_id: int,
    metric: metrics_schemas.MetricCreate,
):
    try:
        return metrics_services.create_metric(run_id, metric)

    except AppError as error:
        raise_http_error(error)


@router.patch("/{metric_id}", response_model=metrics_schemas.MetricResponse)
def update_metric(
    run_id: int,
    metric_id: int,
    metric: metrics_schemas.MetricUpdate,
):
    try:
        return metrics_services.update_metric(run_id, metric_id, metric)

    except AppError as error:
        raise_http_error(error)


@router.delete("/{metric_id}", status_code=204)
def delete_metric(run_id: int, metric_id: int):
    try:
        return metrics_services.delete_metric(run_id, metric_id)

    except AppError as error:
        raise_http_error(error)
