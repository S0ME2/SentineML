from sqlalchemy import exists, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.application.exceptions import parameters as exc
from app.application.exceptions import runs as run_exc
from app.application.ports.repositories import ParameterRepository
from app.domain.parameters import Parameter
from app.infrastructure.postgres.integrity import (
    FOREIGN_KEY_VIOLATION,
    UNIQUE_VIOLATION,
    get_constraint_name,
    get_sqlstate,
)
from app.infrastructure.postgres.mappers.parameters import (
    apply_parameter_to_orm,
    new_parameter_to_orm,
    parameter_to_domain,
)
from app.infrastructure.postgres.orm_models.parameters import ParameterORM


class SQLAlchemyParameterRepository(ParameterRepository):
    def __init__(self, session: Session):
        self._session = session

    def list_for_run(self, run_id: int) -> list[Parameter]:
        models = self._session.scalars(
            select(ParameterORM)
            .where(ParameterORM.run_id == run_id)
            .order_by(ParameterORM.id)
        ).all()
        return [parameter_to_domain(model) for model in models]

    def get_for_run(self, run_id: int, parameter_id: int) -> Parameter | None:
        model = self._session.scalar(
            select(ParameterORM).where(
                ParameterORM.id == parameter_id,
                ParameterORM.run_id == run_id,
            )
        )
        return None if model is None else parameter_to_domain(model)

    def get_for_run_for_update(
        self,
        run_id: int,
        parameter_id: int,
    ) -> Parameter | None:
        model = self._session.scalar(
            select(ParameterORM)
            .where(
                ParameterORM.id == parameter_id,
                ParameterORM.run_id == run_id,
            )
            .with_for_update()
        )
        return None if model is None else parameter_to_domain(model)

    def exists_for_run(self, run_id: int) -> bool:
        return bool(
            self._session.scalar(select(exists().where(ParameterORM.run_id == run_id)))
        )

    def add(self, parameter: Parameter) -> Parameter:
        model = new_parameter_to_orm(parameter)
        self._session.add(model)
        try:
            self._session.flush()
        except IntegrityError as error:
            constraint = get_constraint_name(error)
            if (
                get_sqlstate(error) == UNIQUE_VIOLATION
                and constraint == "uq_parameters_run_name"
            ):
                raise exc.ParameterAlreadyExists(
                    f"Parameter with name '{parameter.name}' already exists for run "
                    f"with id {parameter.run_id}"
                ) from error
            if (
                get_sqlstate(error) == FOREIGN_KEY_VIOLATION
                and constraint == "fk_parameters_run"
            ):
                raise run_exc.RunNotFound(
                    f"Run with id {parameter.run_id} not found"
                ) from error
            raise
        return parameter_to_domain(model)

    def save(self, parameter: Parameter) -> Parameter:
        if parameter.id is None:
            raise ValueError("Cannot save a parameter without an id")
        model = self._session.get(ParameterORM, parameter.id)
        if model is None or model.run_id != parameter.run_id:
            raise RuntimeError("Parameter disappeared before it could be saved")
        apply_parameter_to_orm(parameter, model)
        try:
            self._session.flush()
        except IntegrityError as error:
            if (
                get_sqlstate(error) == UNIQUE_VIOLATION
                and get_constraint_name(error) == "uq_parameters_run_name"
            ):
                raise exc.ParameterAlreadyExists(
                    f"Parameter with name '{parameter.name}' already exists for run "
                    f"with id {parameter.run_id}"
                ) from error
            raise
        return parameter_to_domain(model)

    def delete(self, run_id: int, parameter_id: int) -> None:
        model = self._session.get(ParameterORM, parameter_id)
        if model is None or model.run_id != run_id:
            raise RuntimeError("Parameter disappeared before it could be deleted")
        self._session.delete(model)
        self._session.flush()
