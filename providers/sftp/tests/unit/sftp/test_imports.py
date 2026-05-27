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

import subprocess
import sys

import pytest


@pytest.mark.parametrize(
    "module_name",
    [
        pytest.param("airflow.providers.sftp.triggers.sftp", id="trigger"),
        pytest.param("airflow.providers.sftp.sensors.sftp", id="sensor"),
    ],
)
def test_imports_do_not_warn_for_deprecated_timezone(module_name):
    result = subprocess.run(
        [
            sys.executable,
            "-W",
            "always",
            "-c",
            f"import {module_name}",
        ],
        capture_output=True,
        text=True,
        check=True,
    )

    assert "airflow.utils.timezone" not in result.stderr
