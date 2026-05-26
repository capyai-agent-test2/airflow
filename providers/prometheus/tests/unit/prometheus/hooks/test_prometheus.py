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

import pytest
from prometheus_client import CollectorRegistry

from airflow.models import Connection
from airflow.providers.prometheus.hooks.prometheus import PrometheusHook


class TestPrometheusHook:
    def test_get_conn_uses_default_http_scheme(self):
        hook = PrometheusHook()
        hook.get_connection = mock.Mock(return_value=Connection(conn_type="prometheus", host="pushgateway"))

        assert hook.get_conn() == "http://pushgateway"

    def test_get_conn_uses_schema_and_port(self):
        hook = PrometheusHook()
        hook.get_connection = mock.Mock(
            return_value=Connection(conn_type="prometheus", schema="https", host="pushgateway", port=9091)
        )

        assert hook.get_conn() == "https://pushgateway:9091"

    def test_get_conn_requires_host(self):
        hook = PrometheusHook()
        hook.get_connection = mock.Mock(return_value=Connection(conn_type="prometheus"))

        with pytest.raises(ValueError, match="must define a host"):
            hook.get_conn()

    @mock.patch("airflow.providers.prometheus.hooks.prometheus.basic_auth_handler")
    @mock.patch("airflow.providers.prometheus.hooks.prometheus.push_to_gateway")
    def test_push_to_gateway_uses_basic_auth_when_credentials_exist(
        self, mock_push_to_gateway, mock_auth_handler
    ):
        connection = Connection(
            conn_type="prometheus",
            schema="https",
            host="pushgateway",
            port=9091,
            login="user",
            password="secret",
        )
        hook = PrometheusHook()
        hook.get_connection = mock.Mock(return_value=connection)
        registry = CollectorRegistry()

        hook.push_to_gateway(
            job="dag_metrics", registry=registry, grouping_key={"dag_id": "example"}, timeout=30
        )

        handler = mock_push_to_gateway.call_args.kwargs["handler"]
        assert callable(handler)
        handler("https://pushgateway:9091", "POST", 30, [], b"body")
        mock_auth_handler.assert_called_once_with(
            "https://pushgateway:9091", "POST", 30, [], b"body", "user", "secret"
        )

    @mock.patch("airflow.providers.prometheus.hooks.prometheus.pushadd_to_gateway")
    def test_pushadd_to_gateway_passes_none_handler_without_credentials(self, mock_pushadd_to_gateway):
        connection = Connection(conn_type="prometheus", host="pushgateway")
        hook = PrometheusHook()
        hook.get_connection = mock.Mock(return_value=connection)
        registry = CollectorRegistry()

        hook.pushadd_to_gateway(job="dag_metrics", registry=registry)

        assert mock_pushadd_to_gateway.call_args.kwargs["handler"] is None

    @mock.patch("airflow.providers.prometheus.hooks.prometheus.delete_from_gateway")
    def test_delete_from_gateway_passes_grouping_key(self, mock_delete_from_gateway):
        connection = Connection(conn_type="prometheus", host="pushgateway")
        hook = PrometheusHook()
        hook.get_connection = mock.Mock(return_value=connection)

        hook.delete_from_gateway(job="dag_metrics", grouping_key={"task_id": "push_metrics"})

        mock_delete_from_gateway.assert_called_once_with(
            gateway="http://pushgateway",
            job="dag_metrics",
            grouping_key={"task_id": "push_metrics"},
            timeout=None,
            handler=None,
        )
