from fastapi import APIRouter, Depends

from app.database import get_db
from app.exceptions.base import AppError
from app.routers.error_handlers import raise_http_error
from app.schemas import models as models_schemas
from app.services import models as models_services

router = APIRouter(prefix="/models", tags=["models"])


@router.get("/", response_model=list[models_schemas.ModelResponse])
def get_models(db=Depends(get_db)):
    try:
        return models_services.get_models(db)

    except AppError as error:
        raise_http_error(error)


@router.get("/{model_id}", response_model=models_schemas.ModelResponse)
def get_model(model_id: int, db=Depends(get_db)):
    try:
        return models_services.get_model(model_id, db)

    except AppError as error:
        raise_http_error(error)


@router.post("/", status_code=201, response_model=models_schemas.ModelResponse)
def create_model(model: models_schemas.ModelCreate, db=Depends(get_db)):
    try:
        return models_services.create_model(model, db)

    except AppError as error:
        raise_http_error(error)


@router.patch("/{model_id}", response_model=models_schemas.ModelResponse)
def update_model(model_id: int, model: models_schemas.ModelUpdate, db=Depends(get_db)):
    try:
        return models_services.update_model(model_id, model, db)

    except AppError as error:
        raise_http_error(error)


@router.delete("/{model_id}", status_code=204)
def delete_model(model_id: int, db=Depends(get_db)):
    try:
        return models_services.delete_model(model_id, db)

    except AppError as error:
        raise_http_error(error)
