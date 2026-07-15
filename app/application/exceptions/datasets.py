from app.application.exceptions.base import (
    BadRequestError,
    ConflictError,
    NotFoundError,
)


class DatasetNotFound(NotFoundError):
    pass


class DatasetAlreadyExists(ConflictError):
    pass


class EmptyDatasetUpdate(BadRequestError):
    pass


class InvalidDatasetData(BadRequestError):
    pass


class DatasetInUse(ConflictError):
    pass
