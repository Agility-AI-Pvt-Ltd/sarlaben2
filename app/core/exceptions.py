from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class AppError(Exception):
    status_code = 400
    message = "Application error"

    def __init__(self, message: str | None = None) -> None:
        self.message = message or self.message


class NotFoundError(AppError):
    status_code = 404
    message = "Resource not found"


class ServiceUnavailableError(AppError):
    status_code = 503
    message = "External service unavailable"


class InvalidVerificationCodeError(AppError):
    status_code = 400
    message = "The verification code is invalid or expired"


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def app_error_handler(_request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.message},
        )
