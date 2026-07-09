from app.exceptions import base


class MetricDirectionNotFound(base.NotFoundError):
    pass


class MetricDirectionAlreadyExists(base.ConflictError):
    pass


class EmptyMetricDirectionUpdate(base.BadRequestError):
    pass


class MetricDirectionInUse(base.ConflictError):
    pass
