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

import json
from unittest import mock

import httpx
import pytest

from airflowctl.api.client import Client, ClientKind
from airflowctl.ctl import cli_parser
from airflowctl.ctl.commands import task_command


class TestTaskCommands:
    parser = cli_parser.get_parser()
    dag_id = "example_dag"
    dag_run_id = "manual__2025-01-01T00:00:00+00:00"

    def test_clear_task_instances(self):
        response_json = {
            "task_instances": [
                {
                    "id": "0194af68-3ef4-7991-a281-1dd7f053a2a0",
                    "dag_id": self.dag_id,
                    "dag_run_id": self.dag_run_id,
                    "task_id": "task_a",
                    "map_index": -1,
                    "logical_date": "2025-01-01T00:00:00+00:00",
                    "run_after": "2025-01-01T00:00:00+00:00",
                    "start_date": None,
                    "end_date": None,
                    "duration": None,
                    "state": None,
                    "try_number": 1,
                    "max_tries": 0,
                    "task_display_name": "task_a",
                    "dag_display_name": self.dag_id,
                    "hostname": None,
                    "unixname": None,
                    "pool": "default_pool",
                    "pool_slots": 1,
                    "queue": "default",
                    "priority_weight": 1,
                    "operator": "EmptyOperator",
                    "operator_name": "EmptyOperator",
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
            ],
            "total_entries": 1,
        }

        def handle_request(request: httpx.Request) -> httpx.Response:
            assert request.method == "POST"
            assert request.url.path == f"/api/v2/dags/{self.dag_id}/clearTaskInstances"
            assert request.headers["content-type"] == "application/json"
            assert json.loads(request.read().decode("utf-8")) == {
                "dry_run": False,
                "only_failed": False,
                "only_running": True,
                "reset_dag_runs": True,
                "task_ids": ["task_a", "task_b"],
                "dag_run_id": self.dag_run_id,
                "include_upstream": True,
                "include_downstream": False,
                "include_future": False,
                "include_past": False,
                "prevent_running_task": False,
            }
            return httpx.Response(200, json=response_json)

        api_client = Client(
            base_url="test://server",
            transport=httpx.MockTransport(handle_request),
            token="",
            kind=ClientKind.CLI,
        )

        args = self.parser.parse_args(
            [
                "tasks",
                "clear",
                "--dag-id",
                self.dag_id,
                "--dag-run-id",
                self.dag_run_id,
                "--task-ids",
                "task_a,task_b",
                "--no-only-failed",
                "--only-running",
                "--upstream",
                "--no-dry-run",
            ]
        )

        with mock.patch("airflowctl.ctl.commands.task_command.AirflowConsole") as mock_console_cls:
            result = task_command.clear(args, api_client=api_client)

        assert len(result) == 1
        assert result[0]["dag_id"] == self.dag_id
        assert result[0]["dag_run_id"] == self.dag_run_id
        assert result[0]["task_id"] == "task_a"
        assert result[0]["task_display_name"] == "task_a"
        assert result[0]["dag_display_name"] == self.dag_id
        mock_console_cls.return_value.print_as.assert_called_once_with(
            data=result,
            output="json",
        )

    def test_clear_task_instances_failure(self, api_client_maker):
        api_client = api_client_maker(
            path=f"/api/v2/dags/{self.dag_id}/clearTaskInstances",
            response_json={"detail": "Dag run not found"},
            expected_http_status_code=404,
            kind=ClientKind.CLI,
        )

        with pytest.raises(SystemExit):
            task_command.clear(
                self.parser.parse_args(
                    [
                        "tasks",
                        "clear",
                        "--dag-id",
                        self.dag_id,
                        "--dag-run-id",
                        self.dag_run_id,
                    ]
                ),
                api_client=api_client,
            )
