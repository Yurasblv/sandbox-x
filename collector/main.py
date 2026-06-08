import uvicorn
from fastapi import FastAPI

from collector.api.routes import router
from collector.core.config import get_settings
from collector.core.errors import register_error_handlers
from collector.core.logging import configure_logging, request_logging_middleware


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)

    app = FastAPI(title=settings.app_name, version="0.1.0")
    app.middleware("http")(request_logging_middleware)
    register_error_handlers(app)

    @app.get("/health", tags=["system"])
    async def health() -> dict[str, str]:
        return {"status": "ok", "provider": settings.twitter_provider}

    app.include_router(router)
    return app


app = create_app()


def run() -> None:
    uvicorn.run("collector.main:app", host="0.0.0.0", port=8000, reload=True)
