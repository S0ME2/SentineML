from app.domain.parameters import Parameter
from app.infrastructure.postgres.orm_models.parameters import ParameterORM


def parameter_to_domain(parameter_orm: ParameterORM) -> Parameter:
    return Parameter(
        id=parameter_orm.id,
        run_id=parameter_orm.run_id,
        name=parameter_orm.name,
        value=parameter_orm.value,
        value_type=parameter_orm.value_type,
        notes=parameter_orm.notes,
    )


def new_parameter_to_orm(parameter: Parameter) -> ParameterORM:
    if parameter.id is not None:
        raise ValueError("A new parameter must not already have an id")
    return ParameterORM(
        run_id=parameter.run_id,
        name=parameter.name,
        value=parameter.value,
        value_type=parameter.value_type,
        notes=parameter.notes,
    )


def apply_parameter_to_orm(
    parameter: Parameter,
    parameter_orm: ParameterORM,
) -> None:
    if parameter.id is None or parameter.id != parameter_orm.id:
        raise ValueError("Domain and ORM parameter ids do not match")
    if parameter.run_id != parameter_orm.run_id:
        raise ValueError("A parameter cannot be moved to another run")
    parameter_orm.name = parameter.name
    parameter_orm.value = parameter.value
    parameter_orm.value_type = parameter.value_type
    parameter_orm.notes = parameter.notes
