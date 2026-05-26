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

import json
from contextlib import suppress
from pathlib import Path
from typing import Any

import yaml

BOOLEAN_STRING_PATTERN = r"^(?:[Tt]|[Tt][Rr][Uu][Ee]|1|[Ff]|[Ff][Aa][Ll][Ss][Ee]|0)$"
INTEGER_STRING_PATTERN = r"^-?\d+$"
FLOAT_STRING_PATTERN = r"^-?(?:\d+(?:\.\d+)?|\.\d+)$"
CONFIG_TEMPLATES_DIR = Path(__file__).parent


def build_option_schema(option_data: dict[str, Any]) -> dict[str, Any]:
    option_schema: dict[str, Any] = {}
    option_type = option_data.get("type", "string")

    if option_type == "boolean":
        option_schema["oneOf"] = [
            {"type": "boolean"},
            {"type": "string", "pattern": BOOLEAN_STRING_PATTERN},
        ]
    elif option_type == "integer":
        option_schema["oneOf"] = [
            {"type": "integer"},
            {"type": "string", "pattern": INTEGER_STRING_PATTERN},
        ]
    elif option_type == "float":
        option_schema["oneOf"] = [
            {"type": "number"},
            {"type": "string", "pattern": FLOAT_STRING_PATTERN},
        ]
    else:
        option_schema["type"] = "string"

    if description := option_data.get("description"):
        option_schema["description"] = description

    default = option_data.get("default")
    if default not in (None, ""):
        if option_type == "integer":
            with suppress(TypeError, ValueError):
                default = int(default)
        elif option_type == "float":
            with suppress(TypeError, ValueError):
                default = float(default)
        option_schema["default"] = default

    if example := option_data.get("example"):
        option_schema["examples"] = [example]

    return option_schema


def build_airflow_config_schema(config: dict[str, Any]) -> dict[str, Any]:
    schema: dict[str, Any] = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "Apache Airflow Configuration",
        "description": "JSON Schema for Apache Airflow configuration file (airflow.cfg)",
        "type": "object",
        "properties": {},
        "additionalProperties": False,
    }

    for section_name, section_data in sorted(config.items()):
        options = section_data.get("options")
        if not options:
            continue

        section_schema: dict[str, Any] = {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        }
        if description := section_data.get("description"):
            section_schema["description"] = description

        for option_name, option_data in sorted(options.items()):
            section_schema["properties"][option_name] = build_option_schema(option_data)

        schema["properties"][section_name] = section_schema

    return schema


def render_airflow_config_schema(config: dict[str, Any]) -> str:
    return json.dumps(build_airflow_config_schema(config), indent=2) + "\n"


def main() -> None:
    config_path = CONFIG_TEMPLATES_DIR / "config.yml"
    schema_path = CONFIG_TEMPLATES_DIR / "schema.json"

    with config_path.open(encoding="utf-8") as config_file:
        config = yaml.safe_load(config_file)

    schema_path.write_text(render_airflow_config_schema(config), encoding="utf-8")
    print(f"Generated {schema_path}")


if __name__ == "__main__":
    main()
