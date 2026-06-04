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

from airflow.providers.common.compat.sdk import AirflowException, TaskDeferred
from airflow.providers.google.cloud.sensors.cloud_sql import CloudSQLNoOperationInProgressSensor
from airflow.providers.google.cloud.triggers.cloud_sql import CloudSQLNoOperationInProgressTrigger

PROJECT_ID = "test-project"
INSTANCE = "test-instance"
TEST_GCP_CONN_ID = "test-gcp-conn-id"
TEST_IMPERSONATION_CHAIN = ["ACCOUNT_1", "ACCOUNT_2", "ACCOUNT_3"]


class TestCloudSQLNoOperationInProgressSensor:
    @mock.patch("airflow.providers.google.cloud.sensors.cloud_sql.CloudSQLHook")
    def test_poke(self, mock_hook):
        task = CloudSQLNoOperationInProgressSensor(
            task_id="task-id",
            project_id=PROJECT_ID,
            instance=INSTANCE,
            gcp_conn_id=TEST_GCP_CONN_ID,
            impersonation_chain=TEST_IMPERSONATION_CHAIN,
        )
        mock_hook.return_value.is_instance_operation_in_progress.return_value = False

        assert task.poke(mock.MagicMock()) is True

        mock_hook.assert_called_once_with(
            api_version="v1beta4",
            gcp_conn_id=TEST_GCP_CONN_ID,
            impersonation_chain=TEST_IMPERSONATION_CHAIN,
        )
        mock_hook.return_value.is_instance_operation_in_progress.assert_called_once_with(
            project_id=PROJECT_ID, instance=INSTANCE
        )

    @mock.patch("airflow.providers.google.cloud.sensors.cloud_sql.CloudSQLHook")
    @mock.patch("airflow.providers.google.cloud.sensors.cloud_sql.CloudSQLNoOperationInProgressSensor.defer")
    def test_execute_finishes_before_defer(self, mock_defer, mock_hook):
        task = CloudSQLNoOperationInProgressSensor(
            task_id="task-id",
            project_id=PROJECT_ID,
            instance=INSTANCE,
            deferrable=True,
        )
        mock_hook.return_value.is_instance_operation_in_progress.return_value = False

        task.execute(mock.MagicMock())

        assert not mock_defer.called

    @mock.patch("airflow.providers.google.cloud.sensors.cloud_sql.CloudSQLHook")
    def test_execute_deferred(self, mock_hook):
        task = CloudSQLNoOperationInProgressSensor(
            task_id="task-id",
            project_id=PROJECT_ID,
            instance=INSTANCE,
            deferrable=True,
        )
        mock_hook.return_value.is_instance_operation_in_progress.return_value = True

        with pytest.raises(TaskDeferred) as exc:
            task.execute(mock.MagicMock())

        assert isinstance(exc.value.trigger, CloudSQLNoOperationInProgressTrigger)

    def test_execute_complete_raises_for_error_event(self):
        task = CloudSQLNoOperationInProgressSensor(
            task_id="task-id",
            project_id=PROJECT_ID,
            instance=INSTANCE,
            deferrable=True,
        )

        with pytest.raises(AirflowException):
            task.execute_complete(context={}, event={"status": "error", "message": "test failure message"})

    def test_execute_complete_raises_for_missing_event(self):
        task = CloudSQLNoOperationInProgressSensor(
            task_id="task-id",
            project_id=PROJECT_ID,
            instance=INSTANCE,
            deferrable=True,
        )

        with pytest.raises(AirflowException):
            task.execute_complete(context={}, event=None)
