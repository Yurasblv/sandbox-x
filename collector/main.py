import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from collector.api.routes import router
from collector.api.system import router as system_router
from collector.core.config import settings
from collector.core.errors import register_error_handlers
from collector.core.logging import configure_logging, request_logging_middleware


def create_app() -> FastAPI:
    configure_logging(settings.app.log_level)

    app = FastAPI(title=settings.app.app_name, version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.app.cors_allow_origins,
        allow_methods=settings.app.cors_allow_methods,
        allow_headers=settings.app.cors_allow_headers,
    )
    app.middleware("http")(request_logging_middleware)
    register_error_handlers(app)

    app.include_router(system_router)
    app.include_router(router)
    return app


app = create_app()


def run() -> None:
    uvicorn.run("collector.main:app", host="0.0.0.0", port=8000, reload=True)
