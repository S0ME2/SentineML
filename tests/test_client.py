import io
import json
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

from sentinelml_client import SentinelMLClient, SentinelMLError


class FakeResponse:
    def __init__(self, body, status=200):
        self.body = body
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return self.body


class ClientTests(unittest.TestCase):
    def test_create_and_lifecycle_helpers_use_api_shapes(self):
        responses = [
            FakeResponse(b'{"id": 1}', 201),
            FakeResponse(b'{"id": 2}', 201),
            FakeResponse(b'{"id": 1}'),
        ]
        with patch("sentinelml_client.urlopen", side_effect=responses) as urlopen:
            client = SentinelMLClient("http://example.test/")

            client.create_project("demo", "description")
            client.create_run(1, 2, 3)
            client.start_run(1)

        self.assertEqual(
            urlopen.call_args_list[0].args[0].full_url, "http://example.test/projects/"
        )
        self.assertEqual(
            json.loads(urlopen.call_args_list[1].args[0].data),
            {
                "project_id": 1,
                "dataset_id": 2,
                "model_id": 3,
                "notes": None,
            },
        )

    def test_log_metric_updates_existing_scalar(self):
        responses = [
            FakeResponse(b'[{"id": 9, "name": "loss", "value": 0.7}]'),
            FakeResponse(b'{"id": 9, "value": 0.4}'),
        ]
        with patch("sentinelml_client.urlopen", side_effect=responses):
            client = SentinelMLClient()

            result = client.log_metric(4, "loss", 0.4)

        self.assertEqual(result["value"], 0.4)

    def test_log_metric_normalizes_names_for_creation_and_update(self):
        responses = [
            FakeResponse(b"[]"),
            FakeResponse(b'{"id": 9, "name": "loss", "value": 0.7}', 201),
            FakeResponse(b'[{"id": 9, "name": "loss", "value": 0.7}]'),
            FakeResponse(b'{"id": 9, "name": "loss", "value": 0.4}'),
        ]
        with patch("sentinelml_client.urlopen", side_effect=responses) as urlopen:
            client = SentinelMLClient()
            first = client.log_metric(4, " \tloss\n", 0.7)
            second = client.log_metric(4, " \tloss\n", 0.4)

        created = urlopen.call_args_list[1].args[0]
        updated = urlopen.call_args_list[3].args[0]
        self.assertEqual(json.loads(created.data)["name"], "loss")
        self.assertEqual(created.method, "POST")
        self.assertEqual(updated.method, "PATCH")
        self.assertTrue(updated.full_url.endswith("/metrics/9"))
        self.assertEqual(json.loads(updated.data), {"value": 0.4})
        self.assertEqual(first["id"], second["id"])
        self.assertEqual(second["value"], 0.4)

    def test_context_completes_on_success_and_fails_without_masking_error(self):
        with patch(
            "sentinelml_client.urlopen",
            side_effect=[FakeResponse(b"{}"), FakeResponse(b"{}")],
        ):
            client = SentinelMLClient()
            with client.experiment_run(7):
                pass

        error = HTTPError(
            "http://example.test/runs/8/fail",
            500,
            "failure",
            {},
            io.BytesIO(b'{"detail":"database unavailable"}'),
        )
        with patch(
            "sentinelml_client.urlopen",
            side_effect=[FakeResponse(b"{}"), error],
        ):
            client = SentinelMLClient()
            with self.assertRaisesRegex(ValueError, "original"):
                with client.experiment_run(8):
                    raise ValueError("original")

    def test_http_error_preserves_status_and_details(self):
        error = HTTPError(
            "http://example.test/runs/3/start",
            422,
            "invalid",
            {},
            io.BytesIO(b'{"detail":"invalid run"}'),
        )
        with patch("sentinelml_client.urlopen", side_effect=error):
            with self.assertRaises(SentinelMLError) as context:
                SentinelMLClient().start_run(3)
        self.assertEqual(context.exception.status_code, 422)
        self.assertEqual(context.exception.details, {"detail": "invalid run"})

    def test_invalid_url_timeout_and_non_finite_json_are_rejected(self):
        with self.assertRaises(ValueError):
            SentinelMLClient("ftp://example.test")
        with self.assertRaises(ValueError):
            SentinelMLClient(timeout=0)
        with self.assertRaises(ValueError):
            SentinelMLClient(timeout=float("inf"))
        with self.assertRaises(ValueError):
            SentinelMLClient().add_parameter(1, "bad", float("nan"))

    def test_oserror_from_urlopen_becomes_client_error(self):
        with patch("sentinelml_client.urlopen", side_effect=TimeoutError("timed out")):
            with self.assertRaises(SentinelMLError) as context:
                SentinelMLClient().start_run(3)
        self.assertIsNone(context.exception.status_code)
        self.assertIn("timed out", str(context.exception))


if __name__ == "__main__":
    unittest.main()
