from app.application.exceptions.base import (
    BadRequestError,
    ConflictError,
    NotFoundError,
)


class ModelNotFound(NotFoundError):
    pass


class ModelAlreadyExists(ConflictError):
    pass


class EmptyModelUpdate(BadRequestError):
    pass


class InvalidModelData(BadRequestError):
    pass


class ModelInUse(ConflictError):
    pass
