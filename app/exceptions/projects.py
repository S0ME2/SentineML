from app.exceptions import base


class ProjectNotFound(base.NotFoundError):
    pass


class ProjectAlreadyExists(base.ConflictError):
    pass


class EmptyProjectUpdate(base.BadRequestError):
    pass


class ProjectInUse(base.ConflictError):
    pass
