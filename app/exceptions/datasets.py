from app.exceptions import base


class DatasetNotFound(base.NotFoundError):
    pass


class DatasetAlreadyExists(base.ConflictError):
    pass


class EmptyDatasetUpdate(base.BadRequestError):
    pass


class DatasetInUse(base.ConflictError):
    pass
