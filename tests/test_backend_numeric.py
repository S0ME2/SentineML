import math
import unittest

from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError

from app.domain.errors import InvalidMetricData, InvalidRunData
from app.domain.metrics import Metric
from app.domain.runs import Run
from app.presentation.api.error_handlers import _safe_validation_errors
from app.presentation.api.schemas.metrics import MetricCreate, MetricUpdate


class MetricNumericValidationTests(unittest.TestCase):
    def test_domain_rejects_non_finite_values(self) -> None:
        for value in (math.nan, math.inf, -math.inf):
            with self.subTest(value=value):
                with self.assertRaisesRegex(InvalidMetricData, "must be finite"):
                    Metric(run_id=1, name="accuracy", value=value)

    def test_domain_rejects_integers_that_overflow_float(self) -> None:
        with self.assertRaisesRegex(InvalidMetricData, "must be finite"):
            Metric(run_id=1, name="accuracy", value=10**400)

    def test_domain_accepts_finite_integer_and_float_values(self) -> None:
        self.assertEqual(
            Metric(run_id=1, name="accuracy", value=1).value,
            1.0,
        )
        self.assertEqual(
            Metric(run_id=1, name="accuracy", value=0.75).value,
            0.75,
        )

    def test_api_schemas_reject_non_finite_values(self) -> None:
        for schema in (MetricCreate, MetricUpdate):
            for value in (math.nan, math.inf, -math.inf):
                with self.subTest(schema=schema.__name__, value=value):
                    with self.assertRaises(ValidationError):
                        if schema is MetricCreate:
                            schema(name="accuracy", value=value)
                        else:
                            schema(value=value)

    def test_validation_details_do_not_reflect_non_finite_input(self) -> None:
        with self.assertRaises(ValidationError) as raised:
            MetricCreate(name="loss", value=math.inf)

        error = RequestValidationError(raised.exception.errors())
        details = _safe_validation_errors(error)
        self.assertEqual(details[0]["type"], "finite_number")
        self.assertNotIn("input", details[0])
        self.assertNotIn("ctx", details[0])

    def test_run_rejects_invalid_status_without_leaking_type_error(self) -> None:
        with self.assertRaisesRegex(InvalidRunData, "Unknown run status"):
            Run(project_id=1, dataset_id=1, model_id=1, status=[])


if __name__ == "__main__":
    unittest.main()
