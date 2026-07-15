from fastapi import APIRouter, Depends, Response, status

from app.application.use_cases.parameters import (
    CreateParameter,
    CreateParameterCommand,
    DeleteParameter,
    GetParameter,
    ListParameters,
    UpdateParameter,
    UpdateParameterCommand,
)
from app.bootstrap import (
    get_create_parameter_use_case,
    get_delete_parameter_use_case,
    get_list_parameters_use_case,
    get_parameter_use_case,
    get_update_parameter_use_case,
)
from app.presentation.api.schemas.parameters import (
    ParameterCreate,
    ParameterResponse,
    ParameterUpdate,
)

router = APIRouter(prefix="/runs/{run_id}/parameters", tags=["parameters"])


@router.get("/", response_model=list[ParameterResponse])
def list_parameters(
    run_id: int,
    use_case: ListParameters = Depends(get_list_parameters_use_case),
):
    return use_case.execute(run_id)


@router.get("/{parameter_id}", response_model=ParameterResponse)
def get_parameter(
    run_id: int,
    parameter_id: int,
    use_case: GetParameter = Depends(get_parameter_use_case),
):
    return use_case.execute(run_id, parameter_id)


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=ParameterResponse,
)
def create_parameter(
    run_id: int,
    parameter: ParameterCreate,
    use_case: CreateParameter = Depends(get_create_parameter_use_case),
):
    return use_case.execute(
        CreateParameterCommand(
            run_id=run_id,
            name=parameter.name,
            value=parameter.value,
            value_type=parameter.value_type,
            notes=parameter.notes,
        )
    )


@router.patch("/{parameter_id}", response_model=ParameterResponse)
def update_parameter(
    run_id: int,
    parameter_id: int,
    parameter: ParameterUpdate,
    use_case: UpdateParameter = Depends(get_update_parameter_use_case),
):
    return use_case.execute(
        UpdateParameterCommand(
            run_id=run_id,
            parameter_id=parameter_id,
            fields=parameter.model_dump(exclude_unset=True),
        )
    )


@router.delete("/{parameter_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_parameter(
    run_id: int,
    parameter_id: int,
    use_case: DeleteParameter = Depends(get_delete_parameter_use_case),
) -> Response:
    use_case.execute(run_id, parameter_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
