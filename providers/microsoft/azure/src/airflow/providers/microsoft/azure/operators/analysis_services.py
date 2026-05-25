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

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Any

from airflow.providers.common.compat.sdk import BaseOperator
from airflow.providers.microsoft.azure.hooks.analysis_services import AzureAnalysisServicesHook

if TYPE_CHECKING:
    from airflow.sdk import Context


class AzureAnalysisServicesRefreshOperator(BaseOperator):
    """
    Trigger an Azure Analysis Services model refresh.

    :param server: Azure Analysis Services server in ``asazure://...`` or REST URL form.
    :param model_name: Model name to refresh.
    :param request_body: Optional REST API refresh payload.
    :param azure_conn_id: Azure connection used for authentication.
    :param timeout: HTTP timeout in seconds.
    """

    template_fields: Sequence[str] = ("server", "model_name", "request_body")
    template_fields_renderers = {"request_body": "json"}

    def __init__(
        self,
        *,
        server: str,
        model_name: str,
        request_body: Mapping[str, Any] | None = None,
        azure_conn_id: str = AzureAnalysisServicesHook.default_conn_name,
        timeout: float = 60,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.server = server
        self.model_name = model_name
        self.request_body = request_body
        self.azure_conn_id = azure_conn_id
        self.timeout = timeout

    def execute(self, context: Context) -> str:
        """Trigger the refresh and return the refresh id."""
        hook = AzureAnalysisServicesHook(azure_conn_id=self.azure_conn_id, timeout=self.timeout)
        refresh_id = hook.trigger_refresh(
            server=self.server,
            model_name=self.model_name,
            request_body=self.request_body,
        )
        self.log.info("Triggered Azure Analysis Services refresh %s", refresh_id)
        return refresh_id
