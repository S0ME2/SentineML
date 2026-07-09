from fastapi import HTTPException

from app.exceptions import AppError, BadRequestError, ConflictError, NotFoundError


def raise_http_error(error: AppError):
    if isinstance(error, NotFoundError):
        raise HTTPException(
            status_code=404,
            detail=error.message,
        )

    if isinstance(error, BadRequestError):
        raise HTTPException(
            status_code=400,
            detail=error.message,
        )

    if isinstance(error, ConflictError):
        raise HTTPException(
            status_code=409,
            detail=error.message,
        )

    raise HTTPException(
        status_code=500,
        detail="Unexpected application error",
    )
