from fastapi import APIRouter

from app.exceptions.base import AppError
from app.routers.error_handlers import raise_http_error
from app.schemas import datasets as datasets_schemas
from app.services import datasets as dataset_services

router = APIRouter(prefix="/datasets", tags=["datasets"])


@router.get("/", response_model=list[datasets_schemas.DatasetResponse])
def get_datasets():
    try:
        return dataset_services.get_datasets()

    except AppError as error:
        raise_http_error(error)


@router.get("/{dataset_id}", response_model=datasets_schemas.DatasetResponse)
def get_dataset(dataset_id: int):
    try:
        return dataset_services.get_dataset(dataset_id)

    except AppError as error:
        raise_http_error(error)


@router.post("/", status_code=201, response_model=datasets_schemas.DatasetResponse)
def create_dataset(dataset: datasets_schemas.DatasetCreate):
    try:
        return dataset_services.create_dataset(dataset)

    except AppError as error:
        raise_http_error(error)


@router.patch("/{dataset_id}", response_model=datasets_schemas.DatasetResponse)
def update_dataset(dataset_id: int, dataset: datasets_schemas.DatasetUpdate):
    try:
        return dataset_services.update_dataset(dataset_id, dataset)

    except AppError as error:
        raise_http_error(error)


@router.delete("/{dataset_id}", status_code=204)
def delete_dataset(dataset_id: int):
    try:
        return dataset_services.delete_dataset(dataset_id)

    except AppError as error:
        raise_http_error(error)
