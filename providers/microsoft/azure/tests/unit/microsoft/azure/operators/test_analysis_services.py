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

from airflow.providers.microsoft.azure.operators.analysis_services import AzureAnalysisServicesRefreshOperator


@mock.patch("airflow.providers.microsoft.azure.operators.analysis_services.AzureAnalysisServicesHook")
def test_execute(mock_hook_cls):
    mock_hook_cls.return_value.trigger_refresh.return_value = "refresh-id"
    operator = AzureAnalysisServicesRefreshOperator(
        task_id="refresh_analysis_services",
        server="asazure://westus.asazure.windows.net/myserver",
        model_name="AdventureWorks",
        request_body={"Type": "Full"},
    )

    refresh_id = operator.execute(context={})

    assert refresh_id == "refresh-id"
    mock_hook_cls.return_value.trigger_refresh.assert_called_once_with(
        server="asazure://westus.asazure.windows.net/myserver",
        model_name="AdventureWorks",
        request_body={"Type": "Full"},
    )
