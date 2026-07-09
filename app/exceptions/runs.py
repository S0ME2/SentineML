from app.exceptions import base


class RunNotFound(base.NotFoundError):
    pass


class RunAlreadyExists(base.ConflictError):
    pass


class EmptyRunUpdate(base.BadRequestError):
    pass


class RunInUse(base.ConflictError):
    pass


class RunStatusError(base.BadRequestError):
    pass


class RunHasNoMetrics(base.ConflictError):
    pass
