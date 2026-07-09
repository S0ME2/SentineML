from app.exceptions import base


class ParameterNotFound(base.NotFoundError):
    pass


class ParameterAlreadyExists(base.ConflictError):
    pass


class EmptyParameterUpdate(base.BadRequestError):
    pass
