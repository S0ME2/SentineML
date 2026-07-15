from app.application.exceptions.base import (
    BadRequestError,
    ConflictError,
    NotFoundError,
)


class MetricNotFound(NotFoundError):
    pass


class MetricAlreadyExists(ConflictError):
    pass


class EmptyMetricUpdate(BadRequestError):
    pass


class InvalidMetricData(BadRequestError):
    pass
