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

from functools import cached_property
from typing import TYPE_CHECKING, Any

from opensearchpy import (
    OpenSearch,
    RequestsAWSV4SignerAuth,
    RequestsHttpConnection,
    Urllib3AWSV4SignerAuth,
    Urllib3HttpConnection,
)

from airflow.providers.amazon.aws.hooks.base_aws import AwsBaseHook
from airflow.providers.common.compat.sdk import AirflowException
from airflow.providers.opensearch.hooks.opensearch import OpenSearchHook

if TYPE_CHECKING:
    from opensearchpy import Connection as OpenSearchConnectionClass


class OpenSearchAWSHook(OpenSearchHook):
    """
    Interact with Amazon OpenSearch using AWS SigV4 authentication.

    This hook reuses the OpenSearch connection details from the OpenSearch
    provider and sources AWS credentials from an AWS connection.

    :param open_search_conn_id: Connection to use with OpenSearch
    :param aws_conn_id: AWS connection used to resolve credentials
    :param region_name: AWS region for request signing. When omitted, the AWS
        connection resolution is used.
    :param service: AWS service name to sign for. Defaults to ``es`` and may be
        set to ``aoss`` for OpenSearch Serverless data-plane requests.
    :param log_query: Whether to log the query used for OpenSearch
    """

    def __init__(
        self,
        open_search_conn_id: str,
        log_query: bool,
        open_search_conn_class: type[OpenSearchConnectionClass] | None = RequestsHttpConnection,
        aws_conn_id: str | None = None,
        region_name: str | None = None,
        service: str | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            open_search_conn_id=open_search_conn_id,
            log_query=log_query,
            open_search_conn_class=open_search_conn_class,
            **kwargs,
        )
        if aws_conn_id is not None:
            self.aws_conn_id = aws_conn_id
        else:
            self.aws_conn_id = self.conn.extra_dejson.get("aws_conn_id", AwsBaseHook.default_conn_name)
        self.signer_region_name = region_name or self.conn.extra_dejson.get("region_name")
        self.service = service or self.conn.extra_dejson.get("service") or "es"

    @cached_property
    def aws_hook(self) -> AwsBaseHook:
        return AwsBaseHook(aws_conn_id=self.aws_conn_id, region_name=self.signer_region_name)

    @cached_property
    def client(self) -> OpenSearch:
        """Build an OpenSearch client authenticated with AWS SigV4."""
        region_name = self.signer_region_name or self.aws_hook.region_name
        if not region_name:
            raise AirflowException("AWS region is required to create an OpenSearch SigV4 client.")

        client_args: dict[str, Any] = dict(
            hosts=[{"host": self.conn.host, "port": self.conn.port}],
            use_ssl=self.use_ssl,
            verify_certs=self.verify_certs,
            connection_class=self.connection_class,
        )

        credentials = self.aws_hook.get_credentials(region_name=region_name)
        if self.connection_class and issubclass(self.connection_class, RequestsHttpConnection):
            client_args["http_auth"] = RequestsAWSV4SignerAuth(credentials, region_name, self.service)
        elif self.connection_class and issubclass(self.connection_class, Urllib3HttpConnection):
            client_args["http_auth"] = Urllib3AWSV4SignerAuth(credentials, region_name, self.service)
        else:
            raise TypeError(
                "OpenSearchAWSHook supports RequestsHttpConnection or Urllib3HttpConnection connection classes."
            )

        return OpenSearch(**client_args)
