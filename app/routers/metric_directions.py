from fastapi import APIRouter, Depends

from app.database import get_db
from app.crud import metric_directions as metric_directions_crud
from app.schemas import metric_directions as metric_directions_schemas

router = APIRouter(prefix="/metric-directions", tags=["metric-directions"])


@router.get(
    "/",
    response_model=list[metric_directions_schemas.MetricDirectionResponse],
)
def get_metric_directions(db=Depends(get_db)):
    return metric_directions_crud.get_metric_directions(db)


@router.get(
    "/{metric_name}",
    response_model=metric_directions_schemas.MetricDirectionResponse,
)
def get_metric_direction(metric_name: str, db=Depends(get_db)):
    return metric_directions_crud.get_metric_direction(metric_name, db)


@router.post(
    "/",
    status_code=201,
    response_model=metric_directions_schemas.MetricDirectionResponse,
)
def create_metric_direction(
    metric_direction: metric_directions_schemas.MetricDirectionCreate,
    db=Depends(get_db),
):
    return metric_directions_crud.create_metric_direction(metric_direction, db)


@router.patch(
    "/{metric_name}",
    response_model=metric_directions_schemas.MetricDirectionResponse,
)
def update_metric_direction(
    metric_name: str,
    metric_direction: metric_directions_schemas.MetricDirectionUpdate,
    db=Depends(get_db),
):
    return metric_directions_crud.update_metric_direction(metric_name, metric_direction, db)


@router.delete("/{metric_name}", status_code=204)
def delete_metric_direction(metric_name: str, db=Depends(get_db)):
    return metric_directions_crud.delete_metric_direction(metric_name, db)
