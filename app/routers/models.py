from fastapi import APIRouter, Depends

from app.database import get_db
from app.crud import models as models_crud
from app.schemas import models as models_schemas

router = APIRouter(prefix="/models", tags=["models"])


@router.get("/", response_model=list[models_schemas.ModelResponse])
def get_models(db=Depends(get_db)):
    return models_crud.get_models(db)


@router.get("/{model_id}", response_model=models_schemas.ModelResponse)
def get_model(model_id: int, db=Depends(get_db)):
    return models_crud.get_model(model_id, db)


@router.post("/", status_code=201, response_model=models_schemas.ModelResponse)
def create_model(model: models_schemas.ModelCreate, db=Depends(get_db)):
    return models_crud.create_model(model, db)


@router.patch("/{model_id}", response_model=models_schemas.ModelResponse)
def update_model(model_id: int, model: models_schemas.ModelUpdate, db=Depends(get_db)):
    return models_crud.update_model(model_id, model, db)


@router.delete("/{model_id}", status_code=204)
def delete_model(model_id: int, db=Depends(get_db)):
    return models_crud.delete_model(model_id, db)
