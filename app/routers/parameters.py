from fastapi import APIRouter, Depends

from app.database import get_db
from app.crud import parameters as parameters_crud
from app.schemas import parameters as parameters_schemas

router = APIRouter(prefix="/runs/{run_id}/parameters", tags=["parameters"])


@router.get("/", response_model=list[parameters_schemas.ParameterResponse])
def get_parameters(run_id: int, db=Depends(get_db)):
    return parameters_crud.get_parameters(run_id, db)


@router.get("/{parameter_id}", response_model=parameters_schemas.ParameterResponse)
def get_parameter(run_id: int, parameter_id: int, db=Depends(get_db)):
    return parameters_crud.get_parameter(run_id, parameter_id, db)


@router.post("/", status_code=201, response_model=parameters_schemas.ParameterResponse)
def create_parameter(
    run_id: int,
    parameter: parameters_schemas.ParameterCreate,
    db=Depends(get_db),
):
    return parameters_crud.create_parameter(run_id, parameter, db)


@router.patch("/{parameter_id}", response_model=parameters_schemas.ParameterResponse)
def update_parameter(
    run_id: int,
    parameter_id: int,
    parameter: parameters_schemas.ParameterUpdate,
    db=Depends(get_db),
):
    return parameters_crud.update_parameter(run_id, parameter_id, parameter, db)


@router.delete("/{parameter_id}", status_code=204)
def delete_parameter(run_id: int, parameter_id: int, db=Depends(get_db)):
    return parameters_crud.delete_parameter(run_id, parameter_id, db)
