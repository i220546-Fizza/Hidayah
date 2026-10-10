"""Domain errors raised by services; mapped to HTTP responses in one place."""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class AppError(Exception):
    status_code = 400
    default_message = "Request could not be completed."

    def __init__(self, message: str | None = None, *, errors: list[str] | None = None) -> None:
        super().__init__(message or self.default_message)
        self.message = message or self.default_message
        self.errors = errors


class ValidationProblem(AppError):
    status_code = 422
    default_message = "Some values are not valid."


class AuthError(AppError):
    status_code = 401
    default_message = "Sign in again to continue."


class PermissionDenied(AppError):
    status_code = 403
    default_message = "You do not have permission to do this."


class NotFound(AppError):
    status_code = 404
    default_message = "Not found."


class Conflict(AppError):
    status_code = 409
    default_message = "That already exists."


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _handle(_: Request, exc: AppError) -> JSONResponse:
        body: dict[str, object] = {"detail": exc.message}
        if exc.errors:
            body["errors"] = exc.errors
        headers = {"WWW-Authenticate": "Bearer"} if exc.status_code == 401 else None
        return JSONResponse(body, status_code=exc.status_code, headers=headers)
