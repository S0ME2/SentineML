from app.exceptions import base


class ModelNotFound(base.NotFoundError):
    pass


class ModelAlreadyExists(base.ConflictError):
    pass


class EmptyModelUpdate(base.BadRequestError):
    pass


class ModelInUse(base.ConflictError):
    pass
