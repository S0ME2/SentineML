from app.application.exceptions.base import (
    BadRequestError,
    ConflictError,
    NotFoundError,
)


class ParameterNotFound(NotFoundError):
    pass


class ParameterAlreadyExists(ConflictError):
    pass


class EmptyParameterUpdate(BadRequestError):
    pass


class InvalidParameterData(BadRequestError):
    pass
