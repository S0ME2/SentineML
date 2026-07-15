from fastapi import APIRouter, Depends, Response, status

from app.application.use_cases.models import (
    CreateModel,
    CreateModelCommand,
    DeleteModel,
    GetModel,
    ListModels,
    UpdateModel,
    UpdateModelCommand,
)
from app.bootstrap import (
    get_create_model_use_case,
    get_delete_model_use_case,
    get_list_models_use_case,
    get_model_use_case,
    get_update_model_use_case,
)
from app.presentation.api.schemas.models import ModelCreate, ModelResponse, ModelUpdate

router = APIRouter(prefix="/models", tags=["models"])


@router.get("/", response_model=list[ModelResponse])
def list_models(use_case: ListModels = Depends(get_list_models_use_case)):
    return use_case.execute()


@router.get("/{model_id}", response_model=ModelResponse)
def get_model(
    model_id: int,
    use_case: GetModel = Depends(get_model_use_case),
):
    return use_case.execute(model_id)


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=ModelResponse)
def create_model(
    model: ModelCreate,
    use_case: CreateModel = Depends(get_create_model_use_case),
):
    return use_case.execute(
        CreateModelCommand(
            name=model.name,
            version=model.version,
            description=model.description,
            model_type=model.model_type,
            metadata=model.metadata,
        )
    )


@router.patch("/{model_id}", response_model=ModelResponse)
def update_model(
    model_id: int,
    model: ModelUpdate,
    use_case: UpdateModel = Depends(get_update_model_use_case),
):
    return use_case.execute(
        UpdateModelCommand(
            model_id=model_id,
            fields=model.model_dump(exclude_unset=True),
        )
    )


@router.delete("/{model_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_model(
    model_id: int,
    use_case: DeleteModel = Depends(get_delete_model_use_case),
) -> Response:
    use_case.execute(model_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
