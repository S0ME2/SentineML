"""Real PostgreSQL/HTTP workflows. Point only at a disposable test instance."""

import json
import os
import unittest
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from uuid import uuid4

from sentinelml_client import SentinelMLClient


@unittest.skipUnless(os.getenv("SENTINELML_TEST_URL"), "set SENTINELML_TEST_URL")
class HTTPWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = os.environ["SENTINELML_TEST_URL"].rstrip("/")

    def request(self, method, path, data=None, expected=200):
        request = Request(
            self.base + path,
            data=json.dumps(data).encode() if data is not None else None,
            headers={"Content-Type": "application/json"},
            method=method,
        )
        try:
            response = urlopen(request, timeout=15)
        except HTTPError as error:
            response = error
        with response:
            body = response.read()
            self.assertEqual(response.status, expected, body.decode(errors="replace"))
            return json.loads(body) if body else None

    def test_tracking_ranking_and_terminal_immutability(self):
        suffix = uuid4().hex[:10]
        project = self.request(
            "POST", "/projects/", {"name": f"integration-{suffix}"}, 201
        )
        dataset = self.request(
            "POST", "/datasets/", {"name": f"data-{suffix}", "version": "1"}, 201
        )
        model = self.request(
            "POST", "/models/", {"name": f"model-{suffix}", "version": "1"}, 201
        )
        metric = f"loss-{suffix}"
        self.request(
            "POST", "/metric-directions/", {"name": metric, "maximize": False}, 201
        )
        run_ids = []
        for value in (0.4, 0.2):
            run = self.request(
                "POST",
                "/runs/",
                {
                    "project_id": project["id"],
                    "dataset_id": dataset["id"],
                    "model_id": model["id"],
                    "notes": "Synthetic integration record",
                },
                201,
            )
            run_ids.append(run["id"])
            path = f"/runs/{run['id']}"
            self.assertEqual(run["status"], "waiting")
            self.request("POST", path + "/start", expected=400)
            self.request(
                "POST", path + "/parameters/", {"name": "seed", "value": "42"}, 201
            )
            started = self.request("POST", path + "/start")
            self.assertEqual(started["status"], "running")
            self.request("POST", path + "/complete", expected=400)
            self.request(
                "POST", path + "/metrics/", {"name": metric, "value": value}, 201
            )
            completed = self.request("POST", path + "/complete")
            self.assertEqual(completed["status"], "completed")
            self.assertIsNotNone(completed["end_time"])
            self.request(
                "POST",
                path + "/metrics/",
                {"name": metric, "value": 0.1},
                expected=400,
            )
            self.request("DELETE", path, expected=400)

        query = urlencode({"metric_name": metric})
        best_path = f"/projects/{project['id']}/best-run?{query}"
        ranking_path = f"/projects/{project['id']}/runs/compare?{query}"
        self.assertEqual(self.request("GET", best_path)["run_id"], run_ids[1])
        ranking = self.request("GET", ranking_path)
        self.assertEqual([item["run_id"] for item in ranking], run_ids[::-1])
        self.request("POST", f"/runs/{run_ids[1]}/ignore?ignore_reason=invalid-split")
        self.assertEqual(self.request("GET", best_path)["run_id"], run_ids[0])
        self.request("POST", f"/runs/{run_ids[1]}/unignore")
        self.assertEqual(self.request("GET", best_path)["run_id"], run_ids[1])

    def test_text_storage_limits_and_normalized_client_logging(self):
        def check_resource(path, payload, limits, *, direction=False):
            created = self.request("POST", path, payload, 201)
            item_path = path + (created["name"] if direction else str(created["id"]))
            for field, limit in limits.items():
                with self.subTest(path=path, field=field):
                    self.assertEqual(len(created[field]), limit)
                    invalid = "я" * (limit + 1)
                    rejected = self.request(
                        "POST", path, payload | {field: invalid}, expected=422
                    )
                    self.assertEqual(rejected["detail"][0]["type"], "string_too_long")
                    if not direction:
                        self.request("PATCH", item_path, {field: invalid}, expected=422)
                        self.assertEqual(self.request("GET", item_path), created)
                        updated = self.request(
                            "PATCH", item_path, {field: payload[field]}
                        )
                        self.assertEqual(updated[field], payload[field])
            return created

        name = uuid4().hex.ljust(255, "я")
        project = check_resource("/projects/", {"name": name}, {"name": 255})
        dataset = check_resource(
            "/datasets/",
            {"name": name, "version": name, "dataset_hash": name},
            {"name": 255, "version": 255, "dataset_hash": 255},
        )
        model = check_resource(
            "/models/",
            {"name": name, "version": name, "model_type": name},
            {"name": 255, "version": 255, "model_type": 255},
        )
        check_resource(
            "/metric-directions/",
            {"name": name, "maximize": False},
            {"name": 255},
            direction=True,
        )
        run = self.request(
            "POST",
            "/runs/",
            {
                "project_id": project["id"],
                "dataset_id": dataset["id"],
                "model_id": model["id"],
            },
            201,
        )
        path = f"/runs/{run['id']}"
        check_resource(
            path + "/parameters/",
            {"name": name, "value": name, "value_type": "я" * 100},
            {"name": 255, "value": 255, "value_type": 100},
        )
        self.request("POST", path + "/start")
        check_resource(path + "/metrics/", {"name": name, "value": 1.0}, {"name": 255})
        metric_name = "client-" + uuid4().hex
        client = SentinelMLClient(self.base)
        client.ensure_metric_direction(metric_name, maximize=False)
        first = client.log_metric(run["id"], f" \t{metric_name}\n", 1.0)
        second = client.log_metric(run["id"], f" \t{metric_name}\n", 0.5)
        self.assertEqual(first["id"], second["id"])
        self.assertEqual(second["value"], 0.5)
        self.assertEqual(second["name"], metric_name)
        self.request("POST", path + "/complete")

    def test_dashboard_assets_and_health(self):
        self.assertEqual(self.request("GET", "/health/db"), {"status": "ok"})
        self.assertEqual(self.request("GET", "/"), {"message": "Welcome to SentinelML"})
        for path, marker in (
            ("/ui/", b"SentinelML"),
            ("/ui/static/app.js", b"fetch"),
            ("/ui/static/styles.css", b"var(--"),
        ):
            with urlopen(self.base + path, timeout=10) as response:
                self.assertEqual(response.status, 200)
                self.assertIn(marker, response.read())

    def test_non_finite_metric_returns_validation_error(self):
        for value in (float("inf"), float("-inf"), float("nan")):
            with self.subTest(value=str(value)):
                result = self.request(
                    "POST",
                    "/runs/1/metrics/",
                    {"name": "loss", "value": value},
                    expected=422,
                )
                self.assertEqual(result["detail"][0]["type"], "finite_number")
                self.assertNotIn("input", result["detail"][0])


if __name__ == "__main__":
    unittest.main()
