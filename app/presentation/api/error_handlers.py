from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.application.exceptions import (
    AppError,
    BadRequestError,
    ConflictError,
    NotFoundError,
)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def handle_application_error(
        request: Request,
        error: AppError,
    ) -> JSONResponse:
        del request

        if isinstance(error, NotFoundError):
            status_code = 404
        elif isinstance(error, BadRequestError):
            status_code = 400
        elif isinstance(error, ConflictError):
            status_code = 409
        else:
            status_code = 500

        detail = error.message if status_code != 500 else "Unexpected application error"
        return JSONResponse(status_code=status_code, content={"detail": detail})
