# syntax=docker/dockerfile:1.7
FROM python:3.12-slim AS builder

WORKDIR /build

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN --mount=type=bind,source=requirements.txt,target=/tmp/requirements.txt \
    pip wheel --no-cache-dir --wheel-dir /build/wheels -r /tmp/requirements.txt



FROM python:3.12-slim AS runner

ENV PYTHONPATH=/SentinelML \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /SentinelML

RUN addgroup --system app \
    && adduser --system --ingroup app app

RUN --mount=type=bind,from=builder,source=/build/wheels,target=/wheels \
    --mount=type=bind,source=requirements.txt,target=/tmp/requirements.txt \
    pip install --no-cache-dir --no-index --find-links=/wheels -r /tmp/requirements.txt

COPY ./app ./app

USER app

EXPOSE 8888

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8888"]