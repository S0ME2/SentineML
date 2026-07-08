from fastapi import FastAPI
from app.routers import (
    datasets,
    health,
    metric_directions,
    metrics,
    models,
    parameters,
    projects,
    runs,
)

app = FastAPI()
app.include_router(health.router)
app.include_router(projects.router)
app.include_router(datasets.router)
app.include_router(models.router)
app.include_router(runs.router)
app.include_router(parameters.router)
app.include_router(metrics.router)
app.include_router(metric_directions.router)


@app.get("/")
def read_root():
    return {"message": "Welcome to SentinelML"}
