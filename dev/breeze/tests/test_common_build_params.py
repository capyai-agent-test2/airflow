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

from unittest.mock import patch

from airflow_breeze.params.build_ci_params import BuildCiParams


def test_ci_build_args_include_proxy_values_from_airflow_env_vars():
    with patch(
        "os.environ",
        {
            "AIRFLOW_HTTP_PROXY": "http://proxy.example.com:8080",
            "AIRFLOW_HTTPS_PROXY": "https://proxy.example.com:8443",
            "AIRFLOW_NO_PROXY": "localhost,127.0.0.1",
        },
    ):
        build_params = BuildCiParams()

    build_args = build_params.prepare_arguments_for_docker_build_command()

    assert "--build-arg" in build_args
    assert "HTTP_PROXY=http://proxy.example.com:8080" in build_args
    assert "HTTPS_PROXY=https://proxy.example.com:8443" in build_args
    assert "NO_PROXY=localhost,127.0.0.1" in build_args
    assert "http_proxy=http://proxy.example.com:8080" in build_args
    assert "https_proxy=https://proxy.example.com:8443" in build_args
    assert "no_proxy=localhost,127.0.0.1" in build_args
