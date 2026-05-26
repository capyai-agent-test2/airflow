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

from unittest import mock

from airflow.sdk.observability.metrics.otel_logger import get_otel_logger

from tests_common.test_utils.config import conf_vars


@mock.patch("airflow.sdk.observability.metrics.otel_logger.otel_logger.get_otel_logger")
def test_get_otel_logger_passes_configured_path(mock_get_logger):
    with conf_vars(
        {
            ("metrics", "otel_host"): "collector",
            ("metrics", "otel_port"): "4318",
            ("metrics", "otel_path"): "/insert/0/opentelemetry/api/v1/push",
        }
    ):
        get_otel_logger()

    assert mock_get_logger.call_args.kwargs["path"] == "/insert/0/opentelemetry/api/v1/push"
