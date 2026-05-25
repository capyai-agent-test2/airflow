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

from collections.abc import Sequence
from typing import TYPE_CHECKING

from airflow.providers.common.compat.sdk import BaseSensorOperator
from airflow.providers.microsoft.azure.hooks.analysis_services import (
    AzureAnalysisServicesHook,
    AzureAnalysisServicesRefreshException,
    AzureAnalysisServicesRefreshStatus,
)

if TYPE_CHECKING:
    from airflow.sdk import Context


class AzureAnalysisServicesRefreshStatusSensor(BaseSensorOperator):
    """
    Wait for an Azure Analysis Services refresh to finish.

    :param server: Azure Analysis Services server in ``asazure://...`` or REST URL form.
    :param model_name: Model name that owns the refresh.
    :param refresh_id: Refresh id returned by ``AzureAnalysisServicesRefreshOperator``.
    :param azure_conn_id: Azure connection used for authentication.
    :param timeout: HTTP timeout in seconds.
    """

    template_fields: Sequence[str] = ("server", "model_name", "refresh_id")

    def __init__(
        self,
        *,
        server: str,
        model_name: str,
        refresh_id: str,
        azure_conn_id: str = AzureAnalysisServicesHook.default_conn_name,
        timeout: float = 60,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.server = server
        self.model_name = model_name
        self.refresh_id = refresh_id
        self.azure_conn_id = azure_conn_id
        self.request_timeout = timeout

    def poke(self, context: Context) -> bool:
        """Poll refresh state until the model reaches a terminal status."""
        hook = AzureAnalysisServicesHook(azure_conn_id=self.azure_conn_id, timeout=self.request_timeout)
        refresh_status = hook.get_refresh_status(
            server=self.server,
            model_name=self.model_name,
            refresh_id=self.refresh_id,
        )
        status = refresh_status.get("status")
        if status in AzureAnalysisServicesRefreshStatus.FAILURE_STATUSES:
            raise AzureAnalysisServicesRefreshException(
                f"Azure Analysis Services refresh {self.refresh_id} finished with status {status}."
            )
        return status == AzureAnalysisServicesRefreshStatus.SUCCEEDED
