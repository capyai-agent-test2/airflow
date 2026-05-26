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

from airflowctl.api.client import ClientKind
from airflowctl.ctl import cli_parser
from airflowctl.ctl.commands import task_command


class TestTaskCommands:
    parser = cli_parser.get_parser()
    dag_id = "test_dag"
    dag_run_id = "test_run"
    task_id = "test_task"

    task_instance_response = {
        "id": "9c230b40-da03-451d-8bd7-be30471be383",
        "task_id": task_id,
        "dag_id": dag_id,
        "dag_run_id": dag_run_id,
        "map_index": -1,
        "logical_date": None,
        "run_after": "2025-01-01T00:00:00+00:00",
        "start_date": None,
        "end_date": None,
        "duration": None,
        "state": "success",
        "try_number": 1,
        "max_tries": 1,
        "task_display_name": task_id,
        "dag_display_name": dag_id,
        "hostname": None,
        "unixname": None,
        "pool": "default_pool",
        "pool_slots": 1,
        "queue": None,
        "priority_weight": None,
        "operator": None,
        "operator_name": None,
        "queued_when": None,
        "scheduled_when": None,
        "pid": None,
        "executor": None,
        "executor_config": "{}",
        "note": None,
        "rendered_map_index": None,
        "rendered_fields": None,
        "trigger": None,
        "triggerer_job": None,
        "dag_version": None,
    }

    def test_task_state(self, api_client_maker, capsys):
        api_client = api_client_maker(
            path=f"/api/v2/dags/{self.dag_id}/dagRuns/{self.dag_run_id}/taskInstances/{self.task_id}",
            response_json=self.task_instance_response,
            expected_http_status_code=200,
            kind=ClientKind.CLI,
        )

        state = task_command.state(
            self.parser.parse_args(["tasks", "state", self.dag_id, self.dag_run_id, self.task_id]),
            api_client=api_client,
        )

        captured = capsys.readouterr()
        assert captured.out.strip() == "success"
        assert state == "success"

    def test_task_state_for_mapped_task(self, api_client_maker, capsys):
        api_client = api_client_maker(
            path=f"/api/v2/dags/{self.dag_id}/dagRuns/{self.dag_run_id}/taskInstances/{self.task_id}/3",
            response_json={**self.task_instance_response, "map_index": 3, "state": "running"},
            expected_http_status_code=200,
            kind=ClientKind.CLI,
        )

        state = task_command.state(
            self.parser.parse_args(
                ["tasks", "state", self.dag_id, self.dag_run_id, self.task_id, "--map-index", "3"]
            ),
            api_client=api_client,
        )

        captured = capsys.readouterr()
        assert captured.out.strip() == "running"
        assert state == "running"
