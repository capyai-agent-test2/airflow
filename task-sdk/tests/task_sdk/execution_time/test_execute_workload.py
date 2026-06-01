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

from airflow.sdk.exceptions import TaskStartAbortedError
from airflow.sdk.execution_time.execute_workload import execute_workload


def test_execute_workload_returns_supervisor_exit_code(monkeypatch):
    run_workload = mock.Mock(return_value=99)
    monkeypatch.setattr("airflow.sdk.log.configure_logging", mock.Mock())
    monkeypatch.setattr("airflow.settings.dispose_orm", mock.Mock())
    monkeypatch.setattr("airflow.executors.base_executor.BaseExecutor.run_workload", run_workload)

    assert execute_workload(mock.Mock()) == 99


def test_execute_workload_maps_task_start_aborted_to_exit_code(monkeypatch):
    monkeypatch.setattr("airflow.sdk.log.configure_logging", mock.Mock())
    monkeypatch.setattr("airflow.settings.dispose_orm", mock.Mock())
    monkeypatch.setattr(
        "airflow.executors.base_executor.BaseExecutor.run_workload",
        mock.Mock(side_effect=TaskStartAbortedError("not runnable")),
    )

    assert execute_workload(mock.Mock()) == TaskStartAbortedError.exit_code
