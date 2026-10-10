from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import health
from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.errors import register_error_handlers
from app.core.logging import configure_logging


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)

    app = FastAPI(
        title="Hidayah API",
        version="0.1.0",
        docs_url="/docs" if settings.env != "production" else None,
        redoc_url=None,
    )

    # Only the listed origins may call the API from a browser.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
        allow_headers=["Authorization", "Content-Type", "X-Hidayah-Client"],
    )

    register_error_handlers(app)
    app.include_router(health.router)
    app.include_router(api_router)
    return app


app = create_app()
