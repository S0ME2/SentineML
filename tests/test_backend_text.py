import unittest

from app.domain.datasets import Dataset
from app.domain.errors import (
    InvalidDatasetData,
    InvalidMetricData,
    InvalidMetricDirectionData,
    InvalidModelData,
    InvalidParameterData,
    InvalidProjectData,
)
from app.domain.metric_directions import MetricDirection
from app.domain.metrics import Metric
from app.domain.models import Model
from app.domain.parameters import Parameter
from app.domain.projects import Project


class TextLengthTests(unittest.TestCase):
    def test_storage_limits_on_construction_and_mutation(self):
        cases = (
            (Project, {"name": "p"}, InvalidProjectData, {"name": (255, "rename")}),
            (
                Dataset,
                {"name": "d", "version": "1"},
                InvalidDatasetData,
                {
                    "name": (255, "rename"),
                    "version": (255, "change_version"),
                    "dataset_hash": (255, "change_dataset_hash"),
                },
            ),
            (
                Model,
                {"name": "m", "version": "1"},
                InvalidModelData,
                {
                    "name": (255, "rename"),
                    "version": (255, "change_version"),
                    "model_type": (255, "change_model_type"),
                },
            ),
            (
                Parameter,
                {"run_id": 1, "name": "p", "value": "1"},
                InvalidParameterData,
                {
                    "name": (255, "rename"),
                    "value": (255, "change_value"),
                    "value_type": (100, "change_value_type"),
                },
            ),
            (
                Metric,
                {"run_id": 1, "name": "m", "value": 1.0},
                InvalidMetricData,
                {"name": (255, "rename")},
            ),
            (
                MetricDirection,
                {"name": "m", "maximize": False},
                InvalidMetricDirectionData,
                {"name": (255, None)},
            ),
        )
        for entity, defaults, error, fields in cases:
            for field, (limit, setter) in fields.items():
                with self.subTest(entity=entity.__name__, field=field):
                    # PostgreSQL limits characters, not UTF-8 bytes.
                    value = "я" * limit
                    instance = entity(**(defaults | {field: value}))
                    self.assertEqual(getattr(instance, field), value)
                    with self.assertRaisesRegex(error, f"at most {limit}"):
                        entity(**(defaults | {field: value + "я"}))
                    if setter:
                        with self.assertRaisesRegex(error, f"at most {limit}"):
                            getattr(instance, setter)(value + "я")
                        self.assertEqual(getattr(instance, field), value)

    def test_unbounded_text_and_name_normalization_remain_supported(self):
        project = Project(name=" " + "я" * 255 + " ", description="x" * 1000)
        self.assertEqual(project.name, "я" * 255)
        self.assertEqual(project.description, "x" * 1000)
        parameter = Parameter(run_id=1, name="p", value="1", notes="x" * 1000)
        self.assertEqual(parameter.notes, "x" * 1000)
