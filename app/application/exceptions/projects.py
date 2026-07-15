from app.application.exceptions.base import (
    BadRequestError,
    ConflictError,
    NotFoundError,
)


class ProjectNotFound(NotFoundError):
    pass


class ProjectAlreadyExists(ConflictError):
    pass


class EmptyProjectUpdate(BadRequestError):
    pass


class InvalidProjectData(BadRequestError):
    pass


class ProjectInUse(ConflictError):
    pass
