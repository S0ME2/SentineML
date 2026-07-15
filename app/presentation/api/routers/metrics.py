from fastapi import APIRouter, Depends, Response, status

from app.application.use_cases.metrics import (
    CreateMetric,
    CreateMetricCommand,
    DeleteMetric,
    GetMetric,
    ListMetrics,
    UpdateMetric,
    UpdateMetricCommand,
)
from app.bootstrap import (
    get_create_metric_use_case,
    get_delete_metric_use_case,
    get_list_metrics_use_case,
    get_metric_use_case,
    get_update_metric_use_case,
)
from app.presentation.api.schemas.metrics import (
    MetricCreate,
    MetricResponse,
    MetricUpdate,
)

router = APIRouter(prefix="/runs/{run_id}/metrics", tags=["metrics"])


@router.get("/", response_model=list[MetricResponse])
def list_metrics(
    run_id: int,
    use_case: ListMetrics = Depends(get_list_metrics_use_case),
):
    return use_case.execute(run_id)


@router.get("/{metric_id}", response_model=MetricResponse)
def get_metric(
    run_id: int,
    metric_id: int,
    use_case: GetMetric = Depends(get_metric_use_case),
):
    return use_case.execute(run_id, metric_id)


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=MetricResponse)
def create_metric(
    run_id: int,
    metric: MetricCreate,
    use_case: CreateMetric = Depends(get_create_metric_use_case),
):
    return use_case.execute(
        CreateMetricCommand(
            run_id=run_id,
            name=metric.name,
            value=metric.value,
            notes=metric.notes,
        )
    )


@router.patch("/{metric_id}", response_model=MetricResponse)
def update_metric(
    run_id: int,
    metric_id: int,
    metric: MetricUpdate,
    use_case: UpdateMetric = Depends(get_update_metric_use_case),
):
    return use_case.execute(
        UpdateMetricCommand(
            run_id=run_id,
            metric_id=metric_id,
            fields=metric.model_dump(exclude_unset=True),
        )
    )


@router.delete("/{metric_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_metric(
    run_id: int,
    metric_id: int,
    use_case: DeleteMetric = Depends(get_delete_metric_use_case),
) -> Response:
    use_case.execute(run_id, metric_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
