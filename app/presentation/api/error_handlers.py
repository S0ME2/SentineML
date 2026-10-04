from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.application.exceptions import (
    AppError,
    BadRequestError,
    ConflictError,
    NotFoundError,
)


def _safe_validation_errors(error: RequestValidationError) -> list[dict[str, object]]:
    """Return validation details without reflecting arbitrary request values."""
    safe_errors = []
    for item in error.errors():
        safe_item = {
            key: value for key, value in item.items() if key not in {"input", "ctx"}
        }
        safe_errors.append(safe_item)
    return safe_errors


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(RequestValidationError)
    async def handle_request_validation_error(
        request: Request,
        error: RequestValidationError,
    ) -> JSONResponse:
        del request
        return JSONResponse(
            status_code=422,
            content={"detail": _safe_validation_errors(error)},
        )

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
