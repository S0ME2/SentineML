from fastapi import APIRouter, Depends

from app.database import get_db
from app.crud import datasets as datasets_crud
from app.schemas import datasets as datasets_schemas

router = APIRouter(prefix="/datasets", tags=["datasets"])


@router.get("/", response_model=list[datasets_schemas.DatasetResponse])
def get_datasets(db=Depends(get_db)):
    return datasets_crud.get_datasets(db)


@router.get("/{dataset_id}", response_model=datasets_schemas.DatasetResponse)
def get_dataset(dataset_id: int, db=Depends(get_db)):
    return datasets_crud.get_dataset(dataset_id, db)


@router.post("/", status_code=201, response_model=datasets_schemas.DatasetResponse)
def create_dataset(dataset: datasets_schemas.DatasetCreate, db=Depends(get_db)):
    return datasets_crud.create_dataset(dataset, db)


@router.patch("/{dataset_id}", response_model=datasets_schemas.DatasetResponse)
def update_dataset(
    dataset_id: int,
    dataset: datasets_schemas.DatasetUpdate,
    db=Depends(get_db),
):
    return datasets_crud.update_dataset(dataset_id, dataset, db)


@router.delete("/{dataset_id}", status_code=204)
def delete_dataset(dataset_id: int, db=Depends(get_db)):
    return datasets_crud.delete_dataset(dataset_id, db)
