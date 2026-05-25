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

from airflow.providers.microsoft.azure.hooks.analysis_services import AzureAnalysisServicesRefreshException
from airflow.providers.microsoft.azure.sensors.analysis_services import (
    AzureAnalysisServicesRefreshStatusSensor,
)


@mock.patch("airflow.providers.microsoft.azure.sensors.analysis_services.AzureAnalysisServicesHook")
def test_poke_in_progress(mock_hook_cls):
    mock_hook_cls.return_value.get_refresh_status.return_value = {"status": "inProgress"}
    sensor = AzureAnalysisServicesRefreshStatusSensor(
        task_id="wait_for_refresh",
        server="asazure://westus.asazure.windows.net/myserver",
        model_name="AdventureWorks",
        refresh_id="refresh-id",
    )

    assert sensor.poke(context={}) is False


@mock.patch("airflow.providers.microsoft.azure.sensors.analysis_services.AzureAnalysisServicesHook")
def test_poke_succeeded(mock_hook_cls):
    mock_hook_cls.return_value.get_refresh_status.return_value = {"status": "succeeded"}
    sensor = AzureAnalysisServicesRefreshStatusSensor(
        task_id="wait_for_refresh",
        server="asazure://westus.asazure.windows.net/myserver",
        model_name="AdventureWorks",
        refresh_id="refresh-id",
    )

    assert sensor.poke(context={}) is True


@mock.patch("airflow.providers.microsoft.azure.sensors.analysis_services.AzureAnalysisServicesHook")
def test_poke_failed(mock_hook_cls):
    mock_hook_cls.return_value.get_refresh_status.return_value = {"status": "failed"}
    sensor = AzureAnalysisServicesRefreshStatusSensor(
        task_id="wait_for_refresh",
        server="asazure://westus.asazure.windows.net/myserver",
        model_name="AdventureWorks",
        refresh_id="refresh-id",
    )

    with pytest.raises(AzureAnalysisServicesRefreshException, match="finished with status failed"):
        sensor.poke(context={})
