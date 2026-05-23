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
from azure.batch import models as batch_models

from airflow.providers.microsoft.azure.triggers.batch import AzureBatchJobTrigger
from airflow.triggers.base import TriggerEvent

JOB_ID = "test-job"
CONN_ID = "azure_batch_default"
POLLING_INTERVAL = 15.0


class TestAzureBatchJobTrigger:
    @staticmethod
    def _set_task_list(mock_hook_cls, value) -> None:
        connection = mock.MagicMock()
        connection.task.list = value
        mock_hook_cls.return_value.connection = connection

    def test_serialize(self):
        trigger = AzureBatchJobTrigger(
            job_id=JOB_ID,
            azure_batch_conn_id=CONN_ID,
            polling_interval=POLLING_INTERVAL,
        )

        actual = trigger.serialize()

        assert isinstance(actual, tuple)
        assert actual[0] == f"{AzureBatchJobTrigger.__module__}.{AzureBatchJobTrigger.__name__}"
        assert actual[1] == {
            "job_id": JOB_ID,
            "azure_batch_conn_id": CONN_ID,
            "polling_interval": POLLING_INTERVAL,
        }

    @pytest.mark.asyncio
    @mock.patch("airflow.providers.microsoft.azure.triggers.batch.AzureBatchHook", autospec=True)
    async def test_run_immediate_success(self, mock_hook_cls):
        self._set_task_list(
            mock_hook_cls,
            mock.MagicMock(
                return_value=[
                    mock.Mock(
                        id="task-1",
                        state=batch_models.TaskState.completed,
                        execution_info=mock.Mock(result=batch_models.TaskExecutionResult.success),
                    )
                ]
            ),
        )

        trigger = AzureBatchJobTrigger(job_id=JOB_ID, azure_batch_conn_id=CONN_ID)

        generator = trigger.run()
        response = await generator.asend(None)

        assert response == TriggerEvent({"status": "success", "job_id": JOB_ID, "failed_tasks": []})

    @pytest.mark.asyncio
    @mock.patch("asyncio.sleep", return_value=None)
    @mock.patch("airflow.providers.microsoft.azure.triggers.batch.AzureBatchHook", autospec=True)
    async def test_run_polls_until_success(self, mock_hook_cls, mock_sleep):
        task_list = mock.MagicMock(
            side_effect=[
                [mock.Mock(id="task-1", state="active")],
                [
                    mock.Mock(
                        id="task-1",
                        state=batch_models.TaskState.completed,
                        execution_info=mock.Mock(result=batch_models.TaskExecutionResult.success),
                    )
                ],
            ]
        )
        self._set_task_list(mock_hook_cls, task_list)

        trigger = AzureBatchJobTrigger(job_id=JOB_ID, azure_batch_conn_id=CONN_ID)

        generator = trigger.run()
        response = await generator.asend(None)

        assert task_list.call_count == 2
        assert mock_sleep.await_count == 1
        assert response == TriggerEvent({"status": "success", "job_id": JOB_ID, "failed_tasks": []})

    @pytest.mark.asyncio
    @mock.patch("airflow.providers.microsoft.azure.triggers.batch.AzureBatchHook", autospec=True)
    async def test_run_reports_failed_tasks(self, mock_hook_cls):
        self._set_task_list(
            mock_hook_cls,
            mock.MagicMock(
                return_value=[
                    mock.Mock(
                        id="task-1",
                        state=batch_models.TaskState.completed,
                        execution_info=mock.Mock(result=batch_models.TaskExecutionResult.failure),
                    )
                ]
            ),
        )

        trigger = AzureBatchJobTrigger(job_id=JOB_ID, azure_batch_conn_id=CONN_ID)

        generator = trigger.run()
        response = await generator.asend(None)

        assert response == TriggerEvent({"status": "success", "job_id": JOB_ID, "failed_tasks": ["task-1"]})

    @pytest.mark.asyncio
    @mock.patch("airflow.providers.microsoft.azure.triggers.batch.AzureBatchHook", autospec=True)
    async def test_run_error(self, mock_hook_cls):
        self._set_task_list(mock_hook_cls, mock.MagicMock(side_effect=RuntimeError("API error")))

        trigger = AzureBatchJobTrigger(job_id=JOB_ID, azure_batch_conn_id=CONN_ID)

        generator = trigger.run()
        response = await generator.asend(None)

        assert response == TriggerEvent({"status": "error", "job_id": JOB_ID, "message": "API error"})
