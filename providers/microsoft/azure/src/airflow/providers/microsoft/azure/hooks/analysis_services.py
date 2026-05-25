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

from collections.abc import Mapping
from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote, urlparse

import httpx
from azure.common.credentials import ServicePrincipalCredentials

from airflow.providers.common.compat.sdk import AirflowException
from airflow.providers.microsoft.azure.hooks.base_azure import AzureBaseHook
from airflow.providers.microsoft.azure.utils import AzureIdentityCredentialAdapter

AAS_TOKEN_SCOPE = "https://*.asazure.windows.net/.default"


class AzureAnalysisServicesRefreshException(AirflowException):
    """Raised when an Azure Analysis Services refresh request fails."""


class AzureAnalysisServicesRefreshStatus:
    """Azure Analysis Services refresh statuses."""

    NOT_STARTED = "notStarted"
    IN_PROGRESS = "inProgress"
    TIMED_OUT = "timedOut"
    CANCELLED = "cancelled"
    FAILED = "failed"
    SUCCEEDED = "succeeded"

    TERMINAL_STATUSES = {TIMED_OUT, CANCELLED, FAILED, SUCCEEDED}
    FAILURE_STATUSES = {TIMED_OUT, CANCELLED, FAILED}


class AzureAnalysisServicesHook(AzureBaseHook):
    """
    Hook for Azure Analysis Services refresh operations.

    :param azure_conn_id: :ref:`Azure connection id<howto/connection:azure>` used for
        Azure AD authentication.
    :param timeout: HTTP timeout in seconds.
    """

    conn_name_attr = "azure_conn_id"
    default_conn_name = "azure_default"
    conn_type = "azure"
    hook_name = "Azure Analysis Services"

    def __init__(self, azure_conn_id: str = default_conn_name, timeout: float = 60) -> None:
        super().__init__(conn_id=azure_conn_id)
        self.timeout = timeout

    @staticmethod
    def get_model_base_url(server: str, model_name: str) -> str:
        """
        Build the Azure Analysis Services model base URL.

        ``server`` accepts either ``asazure://<rollout>.asazure.windows.net/<server-name>`` or
        ``https://<rollout>.asazure.windows.net/servers/<server-name>``.
        """
        parsed = urlparse(server)
        if parsed.scheme == "asazure":
            rollout = parsed.netloc
            server_name = parsed.path.strip("/")
            if rollout and server_name:
                return (
                    f"https://{rollout}/servers/{quote(server_name, safe='')}/models/"
                    f"{quote(model_name, safe='')}"
                )
        elif parsed.scheme in {"http", "https"}:
            normalized = server.rstrip("/")
            if "/servers/" in parsed.path:
                return f"{normalized}/models/{quote(model_name, safe='')}"
        raise ValueError(
            "Azure Analysis Services server must be in the format "
            "'asazure://<rollout>.asazure.windows.net/<server-name>' or "
            "'https://<rollout>.asazure.windows.net/servers/<server-name>'."
        )

    def get_access_token(self) -> str:
        """Get a bearer token for the Azure Analysis Services audience."""
        credential = self.get_credential()
        if isinstance(credential, ServicePrincipalCredentials):
            token = credential.token
            if not token or not token.get("access_token"):
                raise AzureAnalysisServicesRefreshException(
                    "Azure connection did not return an access token."
                )
            return cast("str", token["access_token"])
        if isinstance(credential, AzureIdentityCredentialAdapter):
            token = credential.token
            if not token or not token.get("access_token"):
                credential.signed_session()
                token = credential.token
            if not token or not token.get("access_token"):
                raise AzureAnalysisServicesRefreshException(
                    "Azure connection did not return an access token."
                )
            return cast("str", token["access_token"])
        return credential.get_token(AAS_TOKEN_SCOPE).token

    def run(
        self,
        *,
        method: str,
        server: str,
        model_name: str,
        path: str,
        payload: Mapping[str, Any] | None = None,
        expected_status_codes: set[HTTPStatus] | None = None,
    ) -> httpx.Response:
        """Execute a request against the Azure Analysis Services REST API."""
        url = f"{self.get_model_base_url(server=server, model_name=model_name)}/{path.lstrip('/')}"
        headers = {
            "Authorization": f"Bearer {self.get_access_token()}",
            "Accept": "application/json",
        }
        with httpx.Client(timeout=self.timeout) as client:
            response = client.request(
                method=method.upper(),
                url=url,
                headers=headers,
                json=dict(payload) if payload is not None else None,
            )
        expected = expected_status_codes or {HTTPStatus.OK}
        if HTTPStatus(response.status_code) not in expected:
            raise AzureAnalysisServicesRefreshException(
                f"Azure Analysis Services request failed with status {response.status_code}: {response.text}"
            )
        return response

    def trigger_refresh(
        self, *, server: str, model_name: str, request_body: Mapping[str, Any] | None = None
    ) -> str:
        """
        Trigger a refresh for an Azure Analysis Services model.

        :return: refresh id from the ``Location`` response header.
        """
        response = self.run(
            method="POST",
            server=server,
            model_name=model_name,
            path="refreshes",
            payload=request_body,
            expected_status_codes={HTTPStatus.ACCEPTED},
        )
        location = response.headers.get("Location")
        if not location:
            raise AzureAnalysisServicesRefreshException(
                "Azure Analysis Services refresh response did not include a Location header."
            )
        refresh_id = location.rstrip("/").rsplit("/", 1)[-1]
        if not refresh_id:
            raise AzureAnalysisServicesRefreshException(
                "Azure Analysis Services refresh response did not include a refresh id."
            )
        return refresh_id

    def get_refresh_status(self, *, server: str, model_name: str, refresh_id: str) -> dict[str, Any]:
        """
        Fetch the current refresh status for an Azure Analysis Services refresh id.

        :return: Response payload from ``GET /refreshes/<refresh_id>``.
        """
        response = self.run(
            method="GET",
            server=server,
            model_name=model_name,
            path=f"refreshes/{quote(refresh_id, safe='')}",
        )
        return cast("dict[str, Any]", response.json())
