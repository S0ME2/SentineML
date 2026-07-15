from app.application.exceptions.base import (
    BadRequestError,
    ConflictError,
    NotFoundError,
)


class RunNotFound(NotFoundError):
    pass


class EmptyRunUpdate(BadRequestError):
    pass


class InvalidRunData(BadRequestError):
    pass


class RunStatusError(BadRequestError):
    pass


class RunHasNoMetrics(ConflictError):
    pass


class RunInUse(ConflictError):
    pass
