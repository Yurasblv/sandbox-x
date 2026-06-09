from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from loguru import logger


class AppError(Exception):
    status_code = 500
    error_code = "internal_error"

    def __init__(self, message: str, *, details: dict | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ProviderConfigurationError(AppError):
    status_code = 500
    error_code = "provider_configuration_error"


class ProviderRequestError(AppError):
    status_code = 502
    error_code = "provider_request_error"


class ProviderRateLimitError(AppError):
    status_code = 429
    error_code = "provider_rate_limit"


class ProviderNotFoundError(AppError):
    status_code = 400
    error_code = "provider_not_found"


def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    logger.error(
        "app_error method={} path={} error_code={} status_code={} details={}",
        request.method,
        request.url.path,
        exc.error_code,
        exc.status_code,
        exc.details,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.error_code, "message": exc.message, "details": exc.details}},
    )


def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(
        "unhandled_error method={} path={} error={}",
        request.method,
        request.url.path,
        str(exc),
    )
    return JSONResponse(
        status_code=500,
        content={"error": {"code": "internal_error", "message": "Unexpected server error"}},
    )


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppError, app_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, unhandled_error_handler)  # type: ignore[arg-type]
