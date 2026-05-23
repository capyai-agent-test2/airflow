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

import asyncio
from collections.abc import AsyncIterator
from typing import Any

from azure.batch import models as batch_models

from airflow.providers.microsoft.azure.hooks.batch import AzureBatchHook
from airflow.triggers.base import BaseTrigger, TriggerEvent


class AzureBatchJobTrigger(BaseTrigger):
    """
    Poll an Azure Batch job until all tasks complete.

    :param job_id: Azure Batch job identifier.
    :param azure_batch_conn_id: Azure Batch connection id.
    :param polling_interval: Time in seconds between task polls.
    """

    def __init__(
        self,
        job_id: str,
        azure_batch_conn_id: str = "azure_batch_default",
        polling_interval: float = 15.0,
    ) -> None:
        super().__init__()
        self.job_id = job_id
        self.azure_batch_conn_id = azure_batch_conn_id
        self.polling_interval = polling_interval

    def serialize(self) -> tuple[str, dict[str, Any]]:
        """Serialize trigger arguments and classpath."""
        return (
            f"{self.__class__.__module__}.{self.__class__.__name__}",
            {
                "job_id": self.job_id,
                "azure_batch_conn_id": self.azure_batch_conn_id,
                "polling_interval": self.polling_interval,
            },
        )

    async def run(self) -> AsyncIterator[TriggerEvent]:
        """Poll the Azure Batch job until every task finishes."""
        hook = AzureBatchHook(self.azure_batch_conn_id)
        try:
            while True:
                tasks = await asyncio.to_thread(list, hook.connection.task.list(self.job_id))
                incomplete_tasks = [task for task in tasks if task.state != batch_models.TaskState.completed]

                if not incomplete_tasks:
                    failed_tasks = [
                        task.id
                        for task in tasks
                        if task.execution_info.result == batch_models.TaskExecutionResult.failure
                    ]
                    yield TriggerEvent(
                        {"status": "success", "job_id": self.job_id, "failed_tasks": failed_tasks}
                    )
                    return

                await asyncio.sleep(self.polling_interval)
        except Exception as e:
            yield TriggerEvent({"status": "error", "job_id": self.job_id, "message": str(e)})
