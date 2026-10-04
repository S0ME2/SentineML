"""Small, dependency-free client for the SentinelML HTTP API."""

from __future__ import annotations

import json
import math
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode, urlparse
from urllib.request import Request, urlopen

Transport = Callable[[str, str, Mapping[str, Any] | None], tuple[int, Any]]


class SentinelMLError(RuntimeError):
    """An API or transport error raised by :class:`SentinelMLClient`."""

    def __init__(self, status_code: int | None, details: Any):
        self.status_code = status_code
        self.details = details
        if isinstance(details, dict) and isinstance(details.get("detail"), str):
            message = details["detail"]
        elif isinstance(details, str):
            message = details
        else:
            message = "SentinelML request failed"
        prefix = f"HTTP {status_code}: " if status_code is not None else ""
        super().__init__(prefix + message)


class SentinelMLClient:
    """Synchronous standard-library client for SentinelML's current API."""

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:8888",
        *,
        timeout: float = 10.0,
        transport: Transport | None = None,
    ) -> None:
        parsed_url = urlparse(base_url)
        if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
            raise ValueError("base_url must be an absolute HTTP(S) URL")
        if isinstance(timeout, bool) or not isinstance(timeout, (int, float)):
            raise ValueError("timeout must be a finite positive number")
        if not math.isfinite(timeout) or timeout <= 0:
            raise ValueError("timeout must be a finite positive number")
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._transport = transport

    def _request(
        self,
        method: str,
        path: str,
        payload: Mapping[str, Any] | None = None,
    ) -> Any:
        if self._transport is not None:
            status_code, response = self._transport(method, path, payload)
            if not 200 <= status_code < 300:
                raise SentinelMLError(status_code, response)
            return response

        body = None
        headers = {"Accept": "application/json"}
        if payload is not None:
            body = json.dumps(payload, allow_nan=False).encode("utf-8")
            headers["Content-Type"] = "application/json"
        request = Request(
            self.base_url + path, data=body, headers=headers, method=method
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:  # noqa: S310
                raw = response.read()
                status_code = response.status
        except HTTPError as error:
            raw = error.read()
            raise SentinelMLError(error.code, self._decode(raw)) from error
        except URLError as error:
            raise SentinelMLError(None, str(error.reason)) from error
        except OSError as error:
            raise SentinelMLError(None, str(error)) from error

        if not 200 <= status_code < 300:
            raise SentinelMLError(status_code, self._decode(raw))
        return self._decode(raw)

    @staticmethod
    def _decode(raw: bytes) -> Any:
        if not raw:
            return None
        try:
            return json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return raw.decode("utf-8", errors="replace")

    def create_project(
        self, name: str, description: str | None = None
    ) -> dict[str, Any]:
        return self._request(
            "POST", "/projects/", {"name": name, "description": description}
        )

    def create_dataset(
        self,
        name: str,
        version: str,
        *,
        description: str | None = None,
        dataset_hash: str | None = None,
        source: str | None = None,
        metadata: str | None = None,
    ) -> dict[str, Any]:
        return self._request(
            "POST",
            "/datasets/",
            {
                "name": name,
                "version": version,
                "description": description,
                "dataset_hash": dataset_hash,
                "source": source,
                "metadata": metadata,
            },
        )

    def create_model(
        self,
        name: str,
        version: str,
        *,
        description: str | None = None,
        model_type: str | None = None,
        metadata: str | None = None,
    ) -> dict[str, Any]:
        return self._request(
            "POST",
            "/models/",
            {
                "name": name,
                "version": version,
                "description": description,
                "model_type": model_type,
                "metadata": metadata,
            },
        )

    def create_metric_direction(self, name: str, *, maximize: bool) -> dict[str, Any]:
        return self._request(
            "POST", "/metric-directions/", {"name": name, "maximize": maximize}
        )

    def ensure_metric_direction(self, name: str, *, maximize: bool) -> dict[str, Any]:
        """Get a direction or create it, rejecting an existing mismatch."""
        try:
            direction = self._request(
                "GET", f"/metric-directions/{quote(name, safe='')}"
            )
        except SentinelMLError as error:
            if error.status_code != 404:
                raise
            return self.create_metric_direction(name, maximize=maximize)
        if direction["maximize"] != maximize:
            raise ValueError(
                f"Metric direction '{name}' already exists with "
                f"maximize={direction['maximize']}"
            )
        return direction

    def create_run(
        self,
        project_id: int,
        dataset_id: int,
        model_id: int,
        *,
        notes: str | None = None,
    ) -> dict[str, Any]:
        return self._request(
            "POST",
            "/runs/",
            {
                "project_id": project_id,
                "dataset_id": dataset_id,
                "model_id": model_id,
                "notes": notes,
            },
        )

    def add_parameter(
        self,
        run_id: int,
        name: str,
        value: Any,
        *,
        value_type: str | None = None,
        notes: str | None = None,
    ) -> dict[str, Any]:
        if not isinstance(value, str):
            value = json.dumps(
                value, allow_nan=False, separators=(",", ":"), sort_keys=True
            )
        return self._request(
            "POST",
            f"/runs/{run_id}/parameters/",
            {"name": name, "value": value, "value_type": value_type, "notes": notes},
        )

    def start_run(self, run_id: int) -> dict[str, Any]:
        return self._request("POST", f"/runs/{run_id}/start")

    def log_metric(
        self,
        run_id: int,
        name: str,
        value: float,
        *,
        notes: str | None = None,
    ) -> dict[str, Any]:
        """Create or update one scalar metric using the existing API endpoints.

        SentinelML currently stores one scalar row per metric name. This helper
        updates that row when present; it does not provide metric time series.
        """
        name = name.strip()
        metrics = self._request("GET", f"/runs/{run_id}/metrics/")
        existing = next((metric for metric in metrics if metric["name"] == name), None)
        if existing is None:
            return self._request(
                "POST",
                f"/runs/{run_id}/metrics/",
                {"name": name, "value": value, "notes": notes},
            )
        payload: dict[str, Any] = {"value": value}
        if notes is not None:
            payload["notes"] = notes
        return self._request(
            "PATCH", f"/runs/{run_id}/metrics/{existing['id']}", payload
        )

    def complete_run(self, run_id: int) -> dict[str, Any]:
        return self._request("POST", f"/runs/{run_id}/complete")

    def fail_run(self, run_id: int, reason: str) -> dict[str, Any]:
        query = urlencode({"reason": reason})
        return self._request("POST", f"/runs/{run_id}/fail?{query}")

    def experiment_run(self, run_id: int) -> "ExperimentRun":
        return ExperimentRun(self, run_id)


@dataclass
class ExperimentRun:
    """Context manager for an already-created waiting run."""

    client: SentinelMLClient
    run_id: int

    def __enter__(self) -> "ExperimentRun":
        self.client.start_run(self.run_id)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: Any,
    ) -> bool:
        if exc is None:
            self.client.complete_run(self.run_id)
            return False
        try:
            self.client.fail_run(self.run_id, f"{exc_type.__name__}: {exc}")
        except Exception:
            # Preserve the training exception if the best-effort failure update fails.
            pass
        return False

    def log_metric(
        self, name: str, value: float, *, notes: str | None = None
    ) -> dict[str, Any]:
        return self.client.log_metric(self.run_id, name, value, notes=notes)
