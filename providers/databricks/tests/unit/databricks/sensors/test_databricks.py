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

from airflow.providers.common.compat.sdk import AirflowException, TaskDeferred
from airflow.providers.databricks.hooks.databricks import SQLStatementState
from airflow.providers.databricks.sensors.databricks import (
    DatabricksJobRunSensor,
    DatabricksSQLStatementsSensor,
)
from airflow.providers.databricks.triggers.databricks import DatabricksSQLStatementExecutionTrigger

DEFAULT_CONN_ID = "databricks_default"
STATEMENT = "select * from test.test;"
STATEMENT_ID = "statement_id"
TASK_ID = "task_id"
WAREHOUSE_ID = "warehouse_id"
RUN_ID = 123
TASK_KEY = "extract"


class TestDatabricksJobRunSensor:
    @mock.patch("airflow.providers.databricks.sensors.databricks.DatabricksHook")
    def test_poke_run_success(self, db_mock_class):
        sensor = DatabricksJobRunSensor(task_id=TASK_ID, run_id=RUN_ID)
        db_mock = db_mock_class.return_value
        db_mock.get_run.return_value = {
            "state": {
                "life_cycle_state": "TERMINATED",
                "result_state": "SUCCESS",
                "state_message": "done",
            }
        }
        db_mock.get_run_page_url.return_value = "https://example.com/run"

        assert sensor.poke(None) is True

        db_mock.get_run.assert_called_once_with(RUN_ID)
        db_mock.get_run_page_url.assert_called_once_with(RUN_ID)

    @mock.patch("airflow.providers.databricks.sensors.databricks.DatabricksHook")
    def test_poke_run_failure(self, db_mock_class):
        sensor = DatabricksJobRunSensor(task_id=TASK_ID, run_id=RUN_ID)
        db_mock = db_mock_class.return_value
        db_mock.get_run.return_value = {
            "state": {
                "life_cycle_state": "TERMINATED",
                "result_state": "FAILED",
                "state_message": "top-level failure",
            },
            "tasks": [{"task_key": TASK_KEY, "run_id": 321, "state": {"result_state": "FAILED"}}],
        }
        db_mock.get_run_output.return_value = {"error": "notebook exploded"}
        db_mock.get_run_page_url.return_value = "https://example.com/run"

        with pytest.raises(
            AirflowException,
            match="Databricks run 123 failed with terminal state: .*notebook exploded",
        ):
            sensor.poke(None)

        db_mock.get_run.assert_called_once_with(RUN_ID)
        db_mock.get_run_output.assert_called_once_with(321)
        db_mock.get_run_page_url.assert_called_once_with(RUN_ID)

    @mock.patch("airflow.providers.databricks.sensors.databricks.DatabricksHook")
    def test_poke_task_success_uses_latest_attempt(self, db_mock_class):
        sensor = DatabricksJobRunSensor(task_id=TASK_ID, run_id=RUN_ID, task_key=TASK_KEY)
        db_mock = db_mock_class.return_value
        db_mock.get_run_tasks.return_value = [
            {
                "task_key": TASK_KEY,
                "run_id": 10,
                "start_time": 1,
                "state": {
                    "life_cycle_state": "TERMINATED",
                    "result_state": "FAILED",
                    "state_message": "old failure",
                },
            },
            {
                "task_key": TASK_KEY,
                "run_id": 20,
                "start_time": 2,
                "state": {
                    "life_cycle_state": "TERMINATED",
                    "result_state": "SUCCESS",
                    "state_message": "done",
                },
            },
        ]
        db_mock.get_run_page_url.return_value = "https://example.com/run/20"

        assert sensor.poke(None) is True

        db_mock.get_run_tasks.assert_called_once_with(RUN_ID)
        db_mock.get_run_page_url.assert_called_once_with(20)

    @mock.patch("airflow.providers.databricks.sensors.databricks.DatabricksHook")
    def test_poke_task_success_prefers_latest_run_id_when_start_time_missing(self, db_mock_class):
        sensor = DatabricksJobRunSensor(task_id=TASK_ID, run_id=RUN_ID, task_key=TASK_KEY)
        db_mock = db_mock_class.return_value
        db_mock.get_run_tasks.return_value = [
            {
                "task_key": TASK_KEY,
                "run_id": 10,
                "start_time": 100,
                "state": {
                    "life_cycle_state": "TERMINATED",
                    "result_state": "FAILED",
                    "state_message": "old failure",
                },
            },
            {
                "task_key": TASK_KEY,
                "run_id": 20,
                "state": {
                    "life_cycle_state": "TERMINATED",
                    "result_state": "SUCCESS",
                    "state_message": "done",
                },
            },
        ]
        db_mock.get_run_page_url.return_value = "https://example.com/run/20"

        assert sensor.poke(None) is True

        db_mock.get_run_tasks.assert_called_once_with(RUN_ID)
        db_mock.get_run_page_url.assert_called_once_with(20)

    @mock.patch("airflow.providers.databricks.sensors.databricks.DatabricksHook")
    def test_poke_task_failure(self, db_mock_class):
        sensor = DatabricksJobRunSensor(task_id=TASK_ID, run_id=RUN_ID, task_key=TASK_KEY)
        db_mock = db_mock_class.return_value
        db_mock.get_run_tasks.return_value = [
            {
                "task_key": TASK_KEY,
                "run_id": 20,
                "start_time": 2,
                "state": {
                    "life_cycle_state": "TERMINATED",
                    "result_state": "FAILED",
                    "state_message": "cell failed",
                },
            }
        ]
        db_mock.get_run_page_url.return_value = "https://example.com/run/20"

        with pytest.raises(
            AirflowException,
            match="Databricks task 'extract' in run 123 failed with terminal state: .*cell failed",
        ):
            sensor.poke(None)

        db_mock.get_run_tasks.assert_called_once_with(RUN_ID)
        db_mock.get_run_page_url.assert_called_once_with(20)

    @mock.patch("airflow.providers.databricks.sensors.databricks.DatabricksHook")
    def test_poke_task_missing(self, db_mock_class):
        sensor = DatabricksJobRunSensor(task_id=TASK_ID, run_id=RUN_ID, task_key=TASK_KEY)
        db_mock = db_mock_class.return_value
        db_mock.get_run_tasks.return_value = []

        with pytest.raises(
            AirflowException,
            match="Could not find task_key 'extract' in Databricks run 123.",
        ):
            sensor.poke(None)

        db_mock.get_run_tasks.assert_called_once_with(RUN_ID)


class TestDatabricksSQLStatementsSensor:
    """
    Validate and test the functionality of the DatabricksSQLStatementsSensor. This Sensor borrows heavily
    from the DatabricksSQLStatementOperator, meaning that much of the testing logic is also reused.
    """

    def test_init_statement(self):
        """Test initialization for traditional use-case (statement)."""
        op = DatabricksSQLStatementsSensor(task_id=TASK_ID, statement=STATEMENT, warehouse_id=WAREHOUSE_ID)

        assert op.statement == STATEMENT
        assert op.warehouse_id == WAREHOUSE_ID

    def test_init_statement_id(self):
        """Test initialization when a statement_id is passed, rather than a statement."""
        op = DatabricksSQLStatementsSensor(
            task_id=TASK_ID, statement_id=STATEMENT_ID, warehouse_id=WAREHOUSE_ID
        )

        assert op.statement_id == STATEMENT_ID
        assert op.warehouse_id == WAREHOUSE_ID

    @mock.patch("airflow.providers.databricks.sensors.databricks.DatabricksHook")
    def test_exec_success(self, db_mock_class):
        """
        Test the execute function for non-deferrable execution. This same exact behavior is expected when the
        statement itself fails, so no test_exec_failure_statement is implemented.
        """
        expected_json = {
            "statement": STATEMENT,
            "warehouse_id": WAREHOUSE_ID,
            "catalog": None,
            "schema": None,
            "parameters": None,
            "wait_timeout": "0s",
        }

        op = DatabricksSQLStatementsSensor(task_id=TASK_ID, statement=STATEMENT, warehouse_id=WAREHOUSE_ID)
        db_mock = db_mock_class.return_value
        db_mock.post_sql_statement.return_value = STATEMENT_ID

        op.execute(None)  # No context is being passed in

        db_mock_class.assert_called_once_with(
            DEFAULT_CONN_ID,
            retry_limit=op.databricks_retry_limit,
            retry_delay=op.databricks_retry_delay,
            retry_args=None,
            caller="DatabricksSQLStatementsSensor",
        )

        # Since a statement is being passed in rather than a statement_id, we're asserting that the
        # post_sql_statement method is called once
        db_mock.post_sql_statement.assert_called_once_with(expected_json)
        assert op.statement_id == STATEMENT_ID

    @mock.patch("airflow.providers.databricks.sensors.databricks.DatabricksHook")
    def test_on_kill(self, db_mock_class):
        """
        Test the on_kill method. This is actually part of the DatabricksSQLStatementMixin, so the
        test logic will match that with the same name for DatabricksSQLStatementOperator.
        """
        # Behavior here will remain the same whether a statement or statement_id is passed
        op = DatabricksSQLStatementsSensor(task_id=TASK_ID, statement=STATEMENT, warehouse_id=WAREHOUSE_ID)
        db_mock = db_mock_class.return_value
        op.statement_id = STATEMENT_ID

        # When on_kill is executed, it should call the cancel_sql_statement method
        op.on_kill()
        db_mock.cancel_sql_statement.assert_called_once_with(STATEMENT_ID)

    def test_wait_for_termination_is_default(self):
        """Validate that the default value for wait_for_termination is True."""
        op = DatabricksSQLStatementsSensor(
            task_id=TASK_ID, statement="select * from test.test;", warehouse_id=WAREHOUSE_ID
        )

        assert op.wait_for_termination

    @pytest.mark.parametrize(
        argnames=("statement_state", "expected_poke_result"),
        argvalues=[
            ("RUNNING", False),
            ("SUCCEEDED", True),
        ],
    )
    @mock.patch("airflow.providers.databricks.sensors.databricks.DatabricksHook")
    def test_poke(self, db_mock_class, statement_state, expected_poke_result):
        op = DatabricksSQLStatementsSensor(
            task_id=TASK_ID,
            statement=STATEMENT,
            warehouse_id=WAREHOUSE_ID,
        )
        db_mock = db_mock_class.return_value
        db_mock.get_sql_statement_state.return_value = SQLStatementState(statement_state)

        poke_result = op.poke(None)

        assert poke_result == expected_poke_result

    @mock.patch("airflow.providers.databricks.sensors.databricks.DatabricksHook")
    def test_poke_failure(self, db_mock_class):
        op = DatabricksSQLStatementsSensor(
            task_id=TASK_ID,
            statement=STATEMENT,
            warehouse_id=WAREHOUSE_ID,
        )
        db_mock = db_mock_class.return_value
        db_mock.get_sql_statement_state.return_value = SQLStatementState("FAILED")

        with pytest.raises(AirflowException):
            op.poke(None)

    @mock.patch("airflow.providers.databricks.sensors.databricks.DatabricksHook")
    def test_execute_task_deferred(self, db_mock_class):
        """
        Test that the statement is successfully deferred. This behavior will remain the same whether a
        statement or a statement_id is passed.
        """
        op = DatabricksSQLStatementsSensor(
            task_id=TASK_ID,
            statement=STATEMENT,
            warehouse_id=WAREHOUSE_ID,
            deferrable=True,
        )
        db_mock = db_mock_class.return_value
        db_mock.get_sql_statement_state.return_value = SQLStatementState("RUNNING")

        with pytest.raises(TaskDeferred) as exc:
            op.execute(None)

        assert isinstance(exc.value.trigger, DatabricksSQLStatementExecutionTrigger)
        assert exc.value.method_name == "execute_complete"

    def test_execute_complete_success(self):
        """
        Test the execute_complete function in case the Trigger has returned a successful completion event.
        This method is part of the DatabricksSQLStatementsMixin. Note that this is only being tested when
        in deferrable mode.
        """
        event = {
            "statement_id": STATEMENT_ID,
            "state": SQLStatementState("SUCCEEDED").to_json(),
            "error": {},
        }

        op = DatabricksSQLStatementsSensor(
            task_id=TASK_ID,
            statement=STATEMENT,
            warehouse_id=WAREHOUSE_ID,
            deferrable=True,
        )
        assert op.execute_complete(context=None, event=event) is None

    @mock.patch("airflow.providers.databricks.sensors.databricks.DatabricksHook")
    def test_execute_complete_failure(self, db_mock_class):
        """Test execute_complete function in case the Trigger has returned a failure completion event."""
        event = {
            "statement_id": STATEMENT_ID,
            "state": SQLStatementState("FAILED").to_json(),
            "error": SQLStatementState(
                state="FAILED", error_code="500", error_message="Something Went Wrong"
            ).to_json(),
        }
        op = DatabricksSQLStatementsSensor(
            task_id=TASK_ID,
            statement=STATEMENT,
            warehouse_id=WAREHOUSE_ID,
            deferrable=True,
        )

        with pytest.raises(AirflowException, match="^SQL Statement execution failed with terminal state: .*"):
            op.execute_complete(context=None, event=event)
