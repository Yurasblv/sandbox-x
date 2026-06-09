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
            "- {level} "
            "- {file}:{line} "
            "- {message}"
        ),
    )


async def request_logging_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    started_at = time.perf_counter()
    query_params = _redact_query_params(dict(request.query_params))

    logger.info(
        "api_request_started method={} path={} query_params={}",
        request.method,
        request.url.path,
        query_params,
    )
    try:
        response = await call_next(request)
    except Exception as exc:
        elapsed_ms = round((time.perf_counter() - started_at) * 1000, 2)
        logger.error(
            "api_request_failed method={} path={} query_params={} elapsed_ms={} error={}",
            request.method,
            request.url.path,
            query_params,
            elapsed_ms,
            str(exc),
        )
        raise

    elapsed_ms = round((time.perf_counter() - started_at) * 1000, 2)
    logger.info(
        "api_request_finished method={} path={} status_code={} elapsed_ms={}",
        request.method,
        request.url.path,
        response.status_code,
        elapsed_ms,
    )
    return response


def _redact_query_params(params: dict[str, str]) -> dict[str, str]:
    return {
        key: "***" if key.lower() in SENSITIVE_QUERY_KEYS else value
        for key, value in params.items()
    }
