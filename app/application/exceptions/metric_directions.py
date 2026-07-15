from app.application.exceptions.base import (
    BadRequestError,
    ConflictError,
    NotFoundError,
)


class MetricDirectionNotFound(NotFoundError):
    pass


class MetricDirectionAlreadyExists(ConflictError):
    pass


class EmptyMetricDirectionUpdate(BadRequestError):
    pass


class InvalidMetricDirectionData(BadRequestError):
    pass


class MetricDirectionInUse(ConflictError):
    pass
