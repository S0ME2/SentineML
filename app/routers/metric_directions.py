from fastapi import APIRouter, Depends

from app.database import get_db
from app.exceptions.base import AppError
from app.routers.error_handlers import raise_http_error
from app.schemas import metric_directions as metric_directions_schemas
from app.services import metric_directions as metric_directions_services

router = APIRouter(prefix="/metric-directions", tags=["metric-directions"])


@router.get(
    "/",
    response_model=list[metric_directions_schemas.MetricDirectionResponse],
)
def get_metric_directions(db=Depends(get_db)):
    try:
        return metric_directions_services.get_metric_directions(db)

    except AppError as error:
        raise_http_error(error)


@router.get(
    "/{metric_name}",
    response_model=metric_directions_schemas.MetricDirectionResponse,
)
def get_metric_direction(metric_name: str, db=Depends(get_db)):
    try:
        return metric_directions_services.get_metric_direction(metric_name, db)

    except AppError as error:
        raise_http_error(error)


@router.post(
    "/",
    status_code=201,
    response_model=metric_directions_schemas.MetricDirectionResponse,
)
def create_metric_direction(
    metric_direction: metric_directions_schemas.MetricDirectionCreate,
    db=Depends(get_db),
):
    try:
        return metric_directions_services.create_metric_direction(metric_direction, db)

    except AppError as error:
        raise_http_error(error)


@router.patch(
    "/{metric_name}",
    response_model=metric_directions_schemas.MetricDirectionResponse,
)
def update_metric_direction(
    metric_name: str,
    metric_direction: metric_directions_schemas.MetricDirectionUpdate,
    db=Depends(get_db),
):
    try:
        return metric_directions_services.update_metric_direction(
            metric_name, metric_direction, db
        )

    except AppError as error:
        raise_http_error(error)


@router.delete("/{metric_name}", status_code=204)
def delete_metric_direction(metric_name: str, db=Depends(get_db)):
    try:
        return metric_directions_services.delete_metric_direction(metric_name, db)

    except AppError as error:
        raise_http_error(error)
