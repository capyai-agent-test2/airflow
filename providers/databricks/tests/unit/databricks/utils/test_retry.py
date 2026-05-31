#
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

from datetime import datetime, timezone

import pytest
from tenacity import stop_after_attempt, wait_incrementing

from airflow.providers.databricks.utils.retry import validate_deferrable_databricks_retry_args


@pytest.mark.parametrize(
    "retry_args",
    [
        {"wait": wait_incrementing(start=1, increment=1, max=3)},
        {"stop": stop_after_attempt(3)},
    ],
)
def test_validate_deferrable_databricks_retry_args_rejects_non_serializable_values(retry_args):
    with pytest.raises(
        ValueError,
        match=(
            "DatabricksExecutionTrigger does not support non-serializable "
            "retry_args/databricks_retry_args when deferrable=True"
        ),
    ):
        validate_deferrable_databricks_retry_args(retry_args, component="DatabricksExecutionTrigger")


def test_validate_deferrable_databricks_retry_args_allows_serde_serializable_values():
    validate_deferrable_databricks_retry_args(
        {"deadline": datetime(2026, 5, 31, tzinfo=timezone.utc)},
        component="DatabricksExecutionTrigger",
    )
