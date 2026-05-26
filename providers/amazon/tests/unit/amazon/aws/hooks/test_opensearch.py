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

from unittest import mock

import pytest
from botocore.credentials import ReadOnlyCredentials
from opensearchpy import RequestsHttpConnection, Urllib3HttpConnection

from airflow.models import Connection
from airflow.providers.amazon.aws.hooks.base_aws import AwsBaseHook
from airflow.providers.amazon.aws.hooks.opensearch import OpenSearchAWSHook
from airflow.providers.common.compat.sdk import AirflowException

try:
    import importlib.util

    if not importlib.util.find_spec("airflow.sdk.bases.hook"):
        raise ImportError

    BASEHOOK_PATCH_PATH = "airflow.sdk.bases.hook.BaseHook"
except ImportError:
    BASEHOOK_PATCH_PATH = "airflow.hooks.base.BaseHook"


@pytest.fixture
def opensearch_connection() -> Connection:
    return Connection(
        conn_id="opensearch_default",
        conn_type="opensearch",
        host="search-test.us-east-1.es.amazonaws.com",
        port=443,
        extra={"use_ssl": True, "verify_certs": True},
    )


class TestOpenSearchAWSHook:
    @mock.patch(f"{BASEHOOK_PATCH_PATH}.get_connection")
    def test_preserves_explicit_empty_aws_conn_id(
        self,
        mock_get_connection,
        opensearch_connection,
    ) -> None:
        mock_get_connection.return_value = opensearch_connection

        hook = OpenSearchAWSHook(open_search_conn_id="opensearch_default", log_query=True, aws_conn_id="")

        assert hook.aws_conn_id == ""

    @mock.patch("airflow.providers.amazon.aws.hooks.opensearch.OpenSearch")
    @mock.patch("airflow.providers.amazon.aws.hooks.opensearch.RequestsAWSV4SignerAuth")
    @mock.patch.object(AwsBaseHook, "get_credentials")
    @mock.patch.object(AwsBaseHook, "region_name", new_callable=mock.PropertyMock)
    @mock.patch(f"{BASEHOOK_PATCH_PATH}.get_connection")
    def test_builds_requests_client_with_sigv4_auth(
        self,
        mock_get_connection,
        mock_region_name,
        mock_get_credentials,
        mock_signer,
        mock_open_search,
        opensearch_connection,
    ) -> None:
        credentials = ReadOnlyCredentials("key", "secret", "token")
        mock_get_connection.return_value = opensearch_connection
        mock_region_name.return_value = "us-east-1"
        mock_get_credentials.return_value = credentials

        hook = OpenSearchAWSHook(open_search_conn_id="opensearch_default", log_query=True)
        hook.client

        mock_signer.assert_called_once_with(credentials, "us-east-1", "es")
        mock_open_search.assert_called_once_with(
            hosts=[{"host": "search-test.us-east-1.es.amazonaws.com", "port": 443}],
            use_ssl=True,
            verify_certs=True,
            connection_class=RequestsHttpConnection,
            http_auth=mock_signer.return_value,
        )

    @mock.patch("airflow.providers.amazon.aws.hooks.opensearch.OpenSearch")
    @mock.patch("airflow.providers.amazon.aws.hooks.opensearch.Urllib3AWSV4SignerAuth")
    @mock.patch.object(AwsBaseHook, "get_credentials")
    @mock.patch.object(AwsBaseHook, "region_name", new_callable=mock.PropertyMock)
    @mock.patch(f"{BASEHOOK_PATCH_PATH}.get_connection")
    def test_builds_urllib3_client_for_serverless(
        self,
        mock_get_connection,
        mock_region_name,
        mock_get_credentials,
        mock_signer,
        mock_open_search,
        opensearch_connection,
    ) -> None:
        credentials = ReadOnlyCredentials("key", "secret", "token")
        mock_get_connection.return_value = Connection(
            conn_id="opensearch_default",
            conn_type="opensearch",
            host="test.us-east-1.aoss.amazonaws.com",
            port=443,
            extra={"use_ssl": True, "verify_certs": True, "service": "aoss"},
        )
        mock_region_name.return_value = "us-east-1"
        mock_get_credentials.return_value = credentials

        hook = OpenSearchAWSHook(
            open_search_conn_id="opensearch_default",
            log_query=True,
            open_search_conn_class=Urllib3HttpConnection,
        )
        hook.client

        mock_signer.assert_called_once_with(credentials, "us-east-1", "aoss")
        mock_open_search.assert_called_once_with(
            hosts=[{"host": "test.us-east-1.aoss.amazonaws.com", "port": 443}],
            use_ssl=True,
            verify_certs=True,
            connection_class=Urllib3HttpConnection,
            http_auth=mock_signer.return_value,
        )

    @mock.patch.object(AwsBaseHook, "region_name", new_callable=mock.PropertyMock)
    @mock.patch(f"{BASEHOOK_PATCH_PATH}.get_connection")
    def test_requires_region_name(
        self,
        mock_get_connection,
        mock_region_name,
        opensearch_connection,
    ) -> None:
        mock_get_connection.return_value = opensearch_connection
        mock_region_name.return_value = None

        hook = OpenSearchAWSHook(open_search_conn_id="opensearch_default", log_query=True)

        with pytest.raises(AirflowException, match="AWS region is required"):
            hook.client
