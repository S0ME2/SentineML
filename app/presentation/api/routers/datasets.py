from fastapi import APIRouter, Depends, Response, status

from app.application.use_cases.datasets import (
    CreateDataset,
    CreateDatasetCommand,
    DeleteDataset,
    GetDataset,
    ListDatasets,
    UpdateDataset,
    UpdateDatasetCommand,
)
from app.bootstrap import (
    get_create_dataset_use_case,
    get_dataset_use_case,
    get_delete_dataset_use_case,
    get_list_datasets_use_case,
    get_update_dataset_use_case,
)
from app.presentation.api.schemas.datasets import (
    DatasetCreate,
    DatasetResponse,
    DatasetUpdate,
)

router = APIRouter(prefix="/datasets", tags=["datasets"])


@router.get("/", response_model=list[DatasetResponse])
def list_datasets(use_case: ListDatasets = Depends(get_list_datasets_use_case)):
    return use_case.execute()


@router.get("/{dataset_id}", response_model=DatasetResponse)
def get_dataset(
    dataset_id: int,
    use_case: GetDataset = Depends(get_dataset_use_case),
):
    return use_case.execute(dataset_id)


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=DatasetResponse)
def create_dataset(
    dataset: DatasetCreate,
    use_case: CreateDataset = Depends(get_create_dataset_use_case),
):
    return use_case.execute(
        CreateDatasetCommand(
            name=dataset.name,
            version=dataset.version,
            description=dataset.description,
            dataset_hash=dataset.dataset_hash,
            source=dataset.source,
            metadata=dataset.metadata,
        )
    )


@router.patch("/{dataset_id}", response_model=DatasetResponse)
def update_dataset(
    dataset_id: int,
    dataset: DatasetUpdate,
    use_case: UpdateDataset = Depends(get_update_dataset_use_case),
):
    return use_case.execute(
        UpdateDatasetCommand(
            dataset_id=dataset_id,
            fields=dataset.model_dump(exclude_unset=True),
        )
    )


@router.delete("/{dataset_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_dataset(
    dataset_id: int,
    use_case: DeleteDataset = Depends(get_delete_dataset_use_case),
) -> Response:
    use_case.execute(dataset_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
