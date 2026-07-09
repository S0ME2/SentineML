from fastapi import APIRouter, Depends

from app.database import get_db
from app.exceptions.base import AppError
from app.routers.error_handlers import raise_http_error
from app.schemas import parameters as parameters_schemas
from app.services import parameters as parameters_services

router = APIRouter(prefix="/runs/{run_id}/parameters", tags=["parameters"])


@router.get("/", response_model=list[parameters_schemas.ParameterResponse])
def get_parameters(run_id: int, db=Depends(get_db)):
    try:
        return parameters_services.get_parameters(run_id, db)

    except AppError as error:
        raise_http_error(error)


@router.get("/{parameter_id}", response_model=parameters_schemas.ParameterResponse)
def get_parameter(run_id: int, parameter_id: int, db=Depends(get_db)):
    try:
        return parameters_services.get_parameter(run_id, parameter_id, db)

    except AppError as error:
        raise_http_error(error)


@router.post("/", status_code=201, response_model=parameters_schemas.ParameterResponse)
def create_parameter(
    run_id: int,
    parameter: parameters_schemas.ParameterCreate,
    db=Depends(get_db),
):
    try:
        return parameters_services.create_parameter(run_id, parameter, db)

    except AppError as error:
        raise_http_error(error)


@router.patch("/{parameter_id}", response_model=parameters_schemas.ParameterResponse)
def update_parameter(
    run_id: int,
    parameter_id: int,
    parameter: parameters_schemas.ParameterUpdate,
    db=Depends(get_db),
):
    try:
        return parameters_services.update_parameter(run_id, parameter_id, parameter, db)

    except AppError as error:
        raise_http_error(error)


@router.delete("/{parameter_id}", status_code=204)
def delete_parameter(run_id: int, parameter_id: int, db=Depends(get_db)):
    try:
        return parameters_services.delete_parameter(run_id, parameter_id, db)

    except AppError as error:
        raise_http_error(error)
