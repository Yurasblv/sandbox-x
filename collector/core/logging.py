import sys
import time
from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from loguru import logger

SENSITIVE_QUERY_KEYS = {"api_key", "apikey", "key", "token", "access_token"}


def configure_logging(level: str) -> None:
    logger.remove()
    logger.add(
        sys.stdout,
        level=level.upper(),
        colorize=False,
        serialize=False,
        format=(
            "{time:YYYY-MM-DD HH:mm:ss.SSS} "
            "{level} "
            "{message} "
            "{extra}"
        ),
    )


async def request_logging_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    started_at = time.perf_counter()
    request_logger = logger.bind(
        method=request.method,
        path=request.url.path,
        query_params=_redact_query_params(dict(request.query_params)),
    )

    request_logger.info("api_request_started")
    try:
        response = await call_next(request)
    except Exception:
        elapsed_ms = round((time.perf_counter() - started_at) * 1000, 2)
        request_logger.exception("api_request_failed", elapsed_ms=elapsed_ms)
        raise

    elapsed_ms = round((time.perf_counter() - started_at) * 1000, 2)
    request_logger.bind(
        status_code=response.status_code,
        elapsed_ms=elapsed_ms,
    ).info("api_request_finished")
    return response


def _redact_query_params(params: dict[str, str]) -> dict[str, str]:
    return {
        key: "***" if key.lower() in SENSITIVE_QUERY_KEYS else value
        for key, value in params.items()
    }
