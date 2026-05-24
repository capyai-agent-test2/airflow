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
#
from __future__ import annotations

from collections.abc import Sequence
from functools import cached_property
from typing import TYPE_CHECKING, Any

from airflow.providers.common.compat.sdk import AirflowException, BaseSensorOperator, conf
from airflow.providers.databricks.hooks.databricks import DatabricksHook, RunState, SQLStatementState
from airflow.providers.databricks.operators.databricks import DEFER_METHOD_NAME
from airflow.providers.databricks.utils.databricks import extract_failed_task_errors
from airflow.providers.databricks.utils.mixins import DatabricksSQLStatementsMixin

if TYPE_CHECKING:
    from airflow.providers.common.compat.sdk import Context

XCOM_STATEMENT_ID_KEY = "statement_id"


class DatabricksJobRunSensor(BaseSensorOperator):
    """
    Wait for a Databricks job run or a task within that run to complete.

    :param run_id: Databricks job run ID to monitor.
    :param task_key: Optional Databricks task key inside ``run_id`` to monitor instead of the whole run.
    :param databricks_conn_id: Reference to the Databricks connection.
    :param databricks_retry_limit: Amount of times retry if the Databricks backend is unreachable.
    :param databricks_retry_delay: Number of seconds to wait between retries.
    :param databricks_retry_args: Optional dictionary passed to ``tenacity.Retrying``.
    """

    template_fields: Sequence[str] = ("databricks_conn_id", "run_id", "task_key")
    ui_color = "#1CB1C2"
    ui_fgcolor = "#fff"

    def __init__(
        self,
        *,
        run_id: int,
        task_key: str | None = None,
        databricks_conn_id: str = "databricks_default",
        databricks_retry_limit: int = 3,
        databricks_retry_delay: int = 1,
        databricks_retry_args: dict[Any, Any] | None = None,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.run_id = run_id
        self.task_key = task_key
        self.databricks_conn_id = databricks_conn_id
        self.databricks_retry_limit = databricks_retry_limit
        self.databricks_retry_delay = databricks_retry_delay
        self.databricks_retry_args = databricks_retry_args

    @cached_property
    def _hook(self) -> DatabricksHook:
        return DatabricksHook(
            self.databricks_conn_id,
            retry_limit=self.databricks_retry_limit,
            retry_delay=self.databricks_retry_delay,
            retry_args=self.databricks_retry_args,
            caller="DatabricksJobRunSensor",
        )

    def _get_run_page_url(self, run_id: int) -> str:
        return self._hook.get_run_page_url(run_id)

    def _find_task_run(self) -> dict[str, Any]:
        task_runs = [
            task for task in self._hook.get_run_tasks(self.run_id) if task.get("task_key") == self.task_key
        ]
        if not task_runs:
            raise AirflowException(
                f"Could not find task_key {self.task_key!r} in Databricks run {self.run_id}."
            )

        return max(task_runs, key=lambda task: (task["run_id"], task.get("start_time") or 0))

    def _build_task_error_message(self, run_state: RunState) -> str:
        return (
            f"Databricks task {self.task_key!r} in run {self.run_id} failed with terminal state: "
            f"{run_state} and with the error {run_state.state_message}"
        )

    def _build_run_error_message(self, run_state: RunState, run_info: dict[str, Any]) -> str:
        if run_state.result_state == "FAILED":
            failed_tasks = extract_failed_task_errors(self._hook, run_info, run_state)
            return (
                f"Databricks run {self.run_id} failed with terminal state: {run_state} "
                f"and with the errors {failed_tasks}"
            )
        return (
            f"Databricks run {self.run_id} failed with terminal state: {run_state} "
            f"and with the error {run_state.state_message}"
        )

    def poke(self, context: Context) -> bool:
        if self.task_key:
            task_run = self._find_task_run()
            task_run_id = task_run["run_id"]
            run_state = RunState(**task_run["state"])
            run_page_url = self._get_run_page_url(task_run_id)
            entity_description = f"Databricks task {self.task_key!r} in run {self.run_id}"
            if run_state.is_terminal:
                if run_state.is_successful:
                    self.log.info("%s completed successfully.", entity_description)
                    self.log.info("View run status, Spark UI, and logs at %s", run_page_url)
                    return True
                raise AirflowException(self._build_task_error_message(run_state))
        else:
            run_info = self._hook.get_run(self.run_id)
            run_state = RunState(**run_info["state"])
            run_page_url = self._get_run_page_url(self.run_id)
            entity_description = f"Databricks run {self.run_id}"
            if run_state.is_terminal:
                if run_state.is_successful:
                    self.log.info("%s completed successfully.", entity_description)
                    self.log.info("View run status, Spark UI, and logs at %s", run_page_url)
                    return True
                raise AirflowException(self._build_run_error_message(run_state, run_info))

        self.log.info("%s in run state: %s", entity_description, run_state)
        self.log.info("View run status, Spark UI, and logs at %s", run_page_url)
        return False


class DatabricksSQLStatementsSensor(DatabricksSQLStatementsMixin, BaseSensorOperator):
    """DatabricksSQLStatementsSensor."""

    template_fields: Sequence[str] = (
        "databricks_conn_id",
        "statement",
        "statement_id",
    )
    template_ext: Sequence[str] = (".json-tpl",)
    ui_color = "#1CB1C2"
    ui_fgcolor = "#fff"

    def __init__(
        self,
        warehouse_id: str,
        *,
        statement: str | None = None,
        statement_id: str | None = None,
        catalog: str | None = None,
        schema: str | None = None,
        parameters: list[dict[str, Any]] | None = None,
        databricks_conn_id: str = "databricks_default",
        polling_period_seconds: int = 30,
        databricks_retry_limit: int = 3,
        databricks_retry_delay: int = 1,
        databricks_retry_args: dict[Any, Any] | None = None,
        do_xcom_push: bool = True,
        wait_for_termination: bool = True,
        timeout: float = 3600,
        deferrable: bool = conf.getboolean("operators", "default_deferrable", fallback=False),
        **kwargs,
    ):
        # Handle the scenario where either both statement and statement_id are set/not set
        if statement and statement_id:
            raise AirflowException("Cannot provide both statement and statement_id.")
        if not statement and not statement_id:
            raise AirflowException("One of either statement or statement_id must be provided.")

        if not warehouse_id:
            raise AirflowException("warehouse_id must be provided.")

        super().__init__(**kwargs)

        self.statement = statement
        self.statement_id = statement_id
        self.warehouse_id = warehouse_id
        self.catalog = catalog
        self.schema = schema
        self.parameters = parameters
        self.databricks_conn_id = databricks_conn_id
        self.polling_period_seconds = polling_period_seconds
        self.databricks_retry_limit = databricks_retry_limit
        self.databricks_retry_delay = databricks_retry_delay
        self.databricks_retry_args = databricks_retry_args
        self.wait_for_termination = wait_for_termination
        self.deferrable = deferrable
        self.timeout = timeout
        self.do_xcom_push = do_xcom_push

    @cached_property
    def _hook(self):
        return self._get_hook(caller="DatabricksSQLStatementsSensor")

    def _get_hook(self, caller: str) -> DatabricksHook:
        return DatabricksHook(
            self.databricks_conn_id,
            retry_limit=self.databricks_retry_limit,
            retry_delay=self.databricks_retry_delay,
            retry_args=self.databricks_retry_args,
            caller=caller,
        )

    def execute(self, context: Context):
        if not self.statement_id:
            # Otherwise, we'll go ahead and "submit" the statement
            json = {
                "statement": self.statement,
                "warehouse_id": self.warehouse_id,
                "catalog": self.catalog,
                "schema": self.schema,
                "parameters": self.parameters,
                "wait_timeout": "0s",
            }

            self.statement_id = self._hook.post_sql_statement(json)
            self.log.info("SQL Statement submitted with statement_id: %s", self.statement_id)

        if self.do_xcom_push and context is not None:
            context["ti"].xcom_push(key=XCOM_STATEMENT_ID_KEY, value=self.statement_id)

        # If we're not waiting for the query to complete execution, then we'll go ahead and return. However, a
        # recommendation to use the DatabricksSQLStatementOperator is made in this case
        if not self.wait_for_termination:
            self.log.info(
                "If setting wait_for_termination = False, consider using the DatabricksSQLStatementsOperator instead."
            )
            return

        if self.deferrable:
            self._handle_deferrable_execution(defer_method_name=DEFER_METHOD_NAME)  # type: ignore[misc]

    def poke(self, context: Context):
        """
        Handle non-deferrable Sensor execution.

        :param context: (Context)
        :return: (bool)
        """
        # This is going to very closely mirror the execute_complete
        statement_state: SQLStatementState = self._hook.get_sql_statement_state(self.statement_id)

        if statement_state.is_running:
            self.log.info("SQL Statement with ID %s is running", self.statement_id)
            return False
        if statement_state.is_successful:
            self.log.info("SQL Statement with ID %s completed successfully.", self.statement_id)
            return True
        raise AirflowException(
            f"SQL Statement with ID {statement_state} failed with error: {statement_state.error_message}"
        )
