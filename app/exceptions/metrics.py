from app.exceptions import base


class MetricNotFound(base.NotFoundError):
    pass


class MetricAlreadyExists(base.ConflictError):
    pass


class EmptyMetricUpdate(base.BadRequestError):
    pass


class MetricInUse(base.ConflictError):
    pass
