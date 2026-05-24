# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from airflow.config_templates.generate_schema import (
    BOOLEAN_STRING_VALUES,
    FLOAT_STRING_PATTERN,
    INTEGER_STRING_PATTERN,
    build_option_schema,
    render_airflow_config_schema,
)

CONFIG_TEMPLATES_DIR = Path(__file__).parents[3] / "src" / "airflow" / "config_templates"


@pytest.mark.parametrize(
    ("option_data", "expected_schema"),
    [
        pytest.param(
            {"type": "string", "description": "Text option", "default": "value", "example": "sample"},
            {"type": "string", "description": "Text option", "default": "value", "examples": ["sample"]},
            id="string-option",
        ),
        pytest.param(
            {"type": "boolean", "default": "True"},
            {
                "oneOf": [
                    {"type": "boolean"},
                    {"type": "string", "enum": BOOLEAN_STRING_VALUES},
                ],
                "default": "True",
            },
            id="boolean-option",
        ),
        pytest.param(
            {"type": "integer", "default": "42"},
            {
                "oneOf": [
                    {"type": "integer"},
                    {"type": "string", "pattern": INTEGER_STRING_PATTERN},
                ],
                "default": 42,
            },
            id="integer-option",
        ),
        pytest.param(
            {"type": "float", "default": "3.14"},
            {
                "oneOf": [
                    {"type": "number"},
                    {"type": "string", "pattern": FLOAT_STRING_PATTERN},
                ],
                "default": 3.14,
            },
            id="float-option",
        ),
    ],
)
def test_build_option_schema(option_data: dict, expected_schema: dict):
    assert build_option_schema(option_data) == expected_schema


def test_generated_schema_snapshot_is_up_to_date():
    config_path = CONFIG_TEMPLATES_DIR / "config.yml"
    schema_path = CONFIG_TEMPLATES_DIR / "schema.json"

    with config_path.open(encoding="utf-8") as config_file:
        config = yaml.safe_load(config_file)

    assert schema_path.read_text(encoding="utf-8") == render_airflow_config_schema(config)
