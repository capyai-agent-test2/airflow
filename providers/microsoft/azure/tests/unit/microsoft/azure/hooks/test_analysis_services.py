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
from azure.core.credentials import AccessToken
from httpx import Headers, Response

from airflow.providers.microsoft.azure.hooks.analysis_services import (
    AAS_TOKEN_SCOPE,
    AzureAnalysisServicesHook,
    AzureAnalysisServicesRefreshException,
)


class TestAzureAnalysisServicesHook:
    @pytest.mark.parametrize(
        ("server", "expected"),
        [
            (
                "asazure://westus.asazure.windows.net/myserver",
                "https://westus.asazure.windows.net/servers/myserver/models/AdventureWorks",
            ),
            (
                "https://westus.asazure.windows.net/servers/myserver",
                "https://westus.asazure.windows.net/servers/myserver/models/AdventureWorks",
            ),
        ],
    )
    def test_get_model_base_url(self, server, expected):
        assert AzureAnalysisServicesHook.get_model_base_url(server, "AdventureWorks") == expected

    def test_get_model_base_url_invalid(self):
        with pytest.raises(ValueError, match="Azure Analysis Services server must be in the format"):
            AzureAnalysisServicesHook.get_model_base_url("myserver", "AdventureWorks")

    @mock.patch(
        "airflow.providers.microsoft.azure.hooks.analysis_services.AzureAnalysisServicesHook.get_credential"
    )
    def test_get_access_token(self, mock_get_credential):
        mock_get_credential.return_value.get_token.return_value = AccessToken(token="token", expires_on=1)
        hook = AzureAnalysisServicesHook()

        assert hook.get_access_token() == "token"
        mock_get_credential.return_value.get_token.assert_called_once_with(AAS_TOKEN_SCOPE)

    @mock.patch("airflow.providers.microsoft.azure.hooks.analysis_services.httpx.Client")
    @mock.patch(
        "airflow.providers.microsoft.azure.hooks.analysis_services.AzureAnalysisServicesHook.get_access_token"
    )
    def test_trigger_refresh(self, mock_get_access_token, mock_client_cls):
        mock_get_access_token.return_value = "token"
        response = Response(
            status_code=202,
            headers=Headers(
                {"Location": "https://westus.asazure.windows.net/servers/myserver/models/model/refreshes/abc"}
            ),
            request=mock.MagicMock(),
        )
        mock_client = mock_client_cls.return_value.__enter__.return_value
        mock_client.request.return_value = response

        hook = AzureAnalysisServicesHook()
        refresh_id = hook.trigger_refresh(
            server="asazure://westus.asazure.windows.net/myserver",
            model_name="model",
            request_body={"Type": "Full"},
        )

        assert refresh_id == "abc"
        mock_client.request.assert_called_once()

    @mock.patch("airflow.providers.microsoft.azure.hooks.analysis_services.httpx.Client")
    @mock.patch(
        "airflow.providers.microsoft.azure.hooks.analysis_services.AzureAnalysisServicesHook.get_access_token"
    )
    def test_trigger_refresh_requires_location_header(self, mock_get_access_token, mock_client_cls):
        mock_get_access_token.return_value = "token"
        response = Response(status_code=202, request=mock.MagicMock())
        mock_client = mock_client_cls.return_value.__enter__.return_value
        mock_client.request.return_value = response

        hook = AzureAnalysisServicesHook()
        with pytest.raises(AzureAnalysisServicesRefreshException, match="did not include a Location header"):
            hook.trigger_refresh(
                server="asazure://westus.asazure.windows.net/myserver",
                model_name="model",
            )

    @mock.patch("airflow.providers.microsoft.azure.hooks.analysis_services.httpx.Client")
    @mock.patch(
        "airflow.providers.microsoft.azure.hooks.analysis_services.AzureAnalysisServicesHook.get_access_token"
    )
    def test_get_refresh_status(self, mock_get_access_token, mock_client_cls):
        mock_get_access_token.return_value = "token"
        response = Response(
            status_code=200,
            json={"status": "succeeded"},
            request=mock.MagicMock(),
        )
        mock_client = mock_client_cls.return_value.__enter__.return_value
        mock_client.request.return_value = response

        hook = AzureAnalysisServicesHook()
        status = hook.get_refresh_status(
            server="asazure://westus.asazure.windows.net/myserver",
            model_name="model",
            refresh_id="abc",
        )

        assert status == {"status": "succeeded"}
