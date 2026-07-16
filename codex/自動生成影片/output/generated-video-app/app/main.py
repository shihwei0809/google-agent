from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.routes import router
from app.core.config import settings
from app.core.logging import configure_logging


configure_logging()

app = FastAPI(title=settings.project_name)
app.include_router(router)
app.mount("/output", StaticFiles(directory="output"), name="output")


def run() -> None:
    """Start the FastAPI application with Uvicorn."""
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=False,
    )
