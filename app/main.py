from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.bootstrap import get_engine, get_redis_client
from app.presentation.api.error_handlers import register_exception_handlers
from app.presentation.api.routers import (
    datasets,
    health,
    metric_directions,
    metrics,
    models,
    parameters,
    projects,
    runs,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    del app
    engine = get_engine()
    redis_client = get_redis_client()

    try:
        yield
    finally:
        if redis_client is not None:
            redis_client.close()
        engine.dispose()


app = FastAPI(
    title="SentinelML",
    description="Self-hosted experiment history, lifecycle management, and comparison.",
    version="0.1.0",
    lifespan=lifespan,
)
register_exception_handlers(app)

web_directory = Path(__file__).resolve().parent / "web"
app.mount(
    "/ui/static", StaticFiles(directory=web_directory, check_dir=False), name="web"
)


@app.get("/ui", include_in_schema=False)
def dashboard_redirect() -> RedirectResponse:
    return RedirectResponse("/ui/")


@app.get("/ui/", include_in_schema=False)
def dashboard() -> FileResponse:
    return FileResponse(web_directory / "index.html")


app.include_router(health.router)
app.include_router(projects.router)
app.include_router(datasets.router)
app.include_router(models.router)
app.include_router(runs.router)
app.include_router(parameters.router)
app.include_router(metrics.router)
app.include_router(metric_directions.router)


@app.get("/")
def read_root() -> dict[str, str]:
    return {"message": "Welcome to SentinelML"}
