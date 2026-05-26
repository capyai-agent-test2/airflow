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

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from prometheus_client import CollectorRegistry, delete_from_gateway, push_to_gateway, pushadd_to_gateway
from prometheus_client.exposition import basic_auth_handler

from airflow.providers.common.compat.sdk import BaseHook

if TYPE_CHECKING:
    from airflow.models import Connection

GatewayHandler = Callable[[str, str, float | None, list[tuple[str, str]], bytes], Any]


class PrometheusHook(BaseHook):
    """
    Interact with a Prometheus Pushgateway.

    The Airflow connection should point at the Pushgateway host and port. When
    login and password are set on the connection, basic auth is used for push
    and delete operations.

    :param prometheus_conn_id: :ref:`Prometheus connection id <howto/connection:prometheus>`.
    """

    conn_name_attr = "prometheus_conn_id"
    default_conn_name = "prometheus_default"
    conn_type = "prometheus"
    hook_name = "Prometheus"

    def __init__(self, prometheus_conn_id: str = default_conn_name) -> None:
        super().__init__()
        self.prometheus_conn_id = prometheus_conn_id

    def get_conn(self) -> str:
        """Return the Pushgateway base URL from the configured Airflow connection."""
        connection = self.get_connection(self.prometheus_conn_id)
        return self.get_gateway_url(connection)

    def get_gateway_url(self, connection: Connection) -> str:
        """Build the Pushgateway URL from an Airflow connection."""
        if not connection.host:
            raise ValueError("Prometheus connection must define a host for the Pushgateway.")
        scheme = connection.schema or "http"
        port = f":{connection.port}" if connection.port else ""
        return f"{scheme}://{connection.host}{port}"

    def get_gateway_handler(self, connection: Connection) -> GatewayHandler | None:
        """Return a basic-auth handler when the connection carries credentials."""
        if not connection.login and not connection.password:
            return None

        def handler(
            url: str, method: str, timeout: float | None, headers: list[tuple[str, str]], data: bytes
        ) -> Any:
            return basic_auth_handler(
                url,
                method,
                timeout,
                headers,
                data,
                connection.login or "",
                connection.password or "",
            )

        return handler

    def push_to_gateway(
        self,
        *,
        job: str,
        registry: CollectorRegistry,
        grouping_key: dict[str, str] | None = None,
        timeout: float | None = None,
    ) -> None:
        """Replace metrics for ``job`` in the configured Pushgateway."""
        connection = self.get_connection(self.prometheus_conn_id)
        push_to_gateway(
            gateway=self.get_gateway_url(connection),
            job=job,
            registry=registry,
            grouping_key=grouping_key,
            timeout=timeout,
            handler=self.get_gateway_handler(connection),
        )

    def pushadd_to_gateway(
        self,
        *,
        job: str,
        registry: CollectorRegistry,
        grouping_key: dict[str, str] | None = None,
        timeout: float | None = None,
    ) -> None:
        """Merge metrics for ``job`` into the configured Pushgateway."""
        connection = self.get_connection(self.prometheus_conn_id)
        pushadd_to_gateway(
            gateway=self.get_gateway_url(connection),
            job=job,
            registry=registry,
            grouping_key=grouping_key,
            timeout=timeout,
            handler=self.get_gateway_handler(connection),
        )

    def delete_from_gateway(
        self,
        *,
        job: str,
        grouping_key: dict[str, str] | None = None,
        timeout: float | None = None,
    ) -> None:
        """Delete metrics for ``job`` from the configured Pushgateway."""
        connection = self.get_connection(self.prometheus_conn_id)
        delete_from_gateway(
            gateway=self.get_gateway_url(connection),
            job=job,
            grouping_key=grouping_key,
            timeout=timeout,
            handler=self.get_gateway_handler(connection),
        )
