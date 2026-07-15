from fastapi import APIRouter, Depends, Response, status

from app.application.use_cases.metric_directions import (
    CreateMetricDirection,
    CreateMetricDirectionCommand,
    DeleteMetricDirection,
    GetMetricDirection,
    ListMetricDirections,
    UpdateMetricDirection,
    UpdateMetricDirectionCommand,
)
from app.bootstrap import (
    get_create_metric_direction_use_case,
    get_delete_metric_direction_use_case,
    get_list_metric_directions_use_case,
    get_metric_direction_use_case,
    get_update_metric_direction_use_case,
)
from app.presentation.api.schemas.metric_directions import (
    MetricDirectionCreate,
    MetricDirectionResponse,
    MetricDirectionUpdate,
)

router = APIRouter(prefix="/metric-directions", tags=["metric-directions"])


@router.get("/", response_model=list[MetricDirectionResponse])
def list_metric_directions(
    use_case: ListMetricDirections = Depends(get_list_metric_directions_use_case),
):
    return use_case.execute()


@router.get("/{metric_name}", response_model=MetricDirectionResponse)
def get_metric_direction(
    metric_name: str,
    use_case: GetMetricDirection = Depends(get_metric_direction_use_case),
):
    return use_case.execute(metric_name)


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=MetricDirectionResponse,
)
def create_metric_direction(
    metric_direction: MetricDirectionCreate,
    use_case: CreateMetricDirection = Depends(get_create_metric_direction_use_case),
):
    return use_case.execute(
        CreateMetricDirectionCommand(
            name=metric_direction.name,
            maximize=metric_direction.maximize,
        )
    )


@router.patch("/{metric_name}", response_model=MetricDirectionResponse)
def update_metric_direction(
    metric_name: str,
    metric_direction: MetricDirectionUpdate,
    use_case: UpdateMetricDirection = Depends(get_update_metric_direction_use_case),
):
    return use_case.execute(
        UpdateMetricDirectionCommand(
            metric_name=metric_name,
            maximize=metric_direction.maximize,
        )
    )


@router.delete("/{metric_name}", status_code=status.HTTP_204_NO_CONTENT)
def delete_metric_direction(
    metric_name: str,
    use_case: DeleteMetricDirection = Depends(get_delete_metric_direction_use_case),
) -> Response:
    use_case.execute(metric_name)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
