#!/usr/bin/env python
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
# /// script
# requires-python = ">=3.10,<3.11"
# dependencies = [
#   "rich>=13.6.0",
# ]
# ///
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

from common_prek_utils import AIRFLOW_CORE_SOURCES_PATH, AIRFLOW_ROOT_PATH, console

SCHEMA_PATH = AIRFLOW_CORE_SOURCES_PATH / "airflow" / "config_templates" / "schema.json"
GENERATOR_SCRIPT = AIRFLOW_CORE_SOURCES_PATH / "airflow" / "config_templates" / "generate_schema.py"


def get_uv_binary() -> str:
    project_uv = AIRFLOW_ROOT_PATH / ".venv" / "bin" / "uv"
    if project_uv.exists():
        return str(project_uv)
    uv_from_path = shutil.which("uv")
    if uv_from_path:
        return uv_from_path
    raise RuntimeError("Could not find `uv`. Run `uv sync` to create the project virtualenv first.")


def main() -> int:
    old_content = SCHEMA_PATH.read_text() if SCHEMA_PATH.exists() else None

    subprocess.run(
        [
            get_uv_binary(),
            "run",
            "--project",
            "airflow-core",
            "python",
            str(GENERATOR_SCRIPT),
        ],
        cwd=AIRFLOW_ROOT_PATH,
        check=True,
    )

    new_content = SCHEMA_PATH.read_text()
    if old_content == new_content:
        return 0

    rel_path = Path(SCHEMA_PATH).relative_to(AIRFLOW_ROOT_PATH)
    message = f"Regenerated {rel_path}. Please review the diff and re-stage the file."
    if console:
        console.print(
            f"[yellow]Regenerated[/] [cyan]{rel_path}[/]. Please review the diff and re-stage the file."
        )
    else:
        print(message, file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
