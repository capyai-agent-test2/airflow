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
import textwrap

import pytest

from airflow_e2e_tests.e2e_test_utils.clients import AirflowClient

DAG_ID = "example_xcom_test"


def _execute_dag_test(compose_instance, dag_id: str, *, use_executor: bool) -> str:
    python_code = textwrap.dedent(
        f"""
        import json
        from airflow.dag_processing.dagbag import DagBag

        dagbag = DagBag(dag_folder="/opt/airflow/dags", include_examples=False)
        dag = dagbag.get_dag("{dag_id}")
        if dag is None:
            raise RuntimeError("Dag not found: {dag_id}")

        dag_run = dag.test(use_executor={use_executor})
        print(json.dumps({{"dag_run_id": dag_run.run_id}}))
        """
    )
    stdout, stderr, exit_code = compose_instance.exec_in_container(
        command=["python", "-c", python_code],
        service_name="airflow-scheduler",
    )
    output = stdout.decode() if isinstance(stdout, bytes) else stdout
    error_output = stderr.decode() if isinstance(stderr, bytes) else stderr
    if exit_code != 0:
        raise RuntimeError(
            f"dag.test() failed for {dag_id} with exit code {exit_code}\nstdout:\n{output}\nstderr:\n{error_output}"
        )

    for line in reversed(output.splitlines()):
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        dag_run_id = payload.get("dag_run_id")
        if dag_run_id:
            return dag_run_id

    raise RuntimeError(f"Could not parse Dag run id from dag.test() output for {dag_id}:\n{output}")


class TestDagTest:
    airflow_client = AirflowClient()

    @pytest.mark.parametrize("use_executor", [False, True], ids=["inline", "executor"])
    def test_dag_test_runs_example_xcom_dag(self, compose_instance, use_executor: bool):
        dag_run_id = _execute_dag_test(compose_instance, DAG_ID, use_executor=use_executor)

        dag_run_state = self.airflow_client.wait_for_dag_run(DAG_ID, dag_run_id, timeout=60, check_interval=1)
        assert dag_run_state == "success"

        task_instances = self.airflow_client.get_task_instances(DAG_ID, dag_run_id)["task_instances"]
        assert {task_instance["state"] for task_instance in task_instances} == {"success"}

        xcom_value = self.airflow_client.get_xcom_value(
            dag_id=DAG_ID,
            task_id="bash_push",
            key="manually_pushed_value",
            run_id=dag_run_id,
        )
        assert xcom_value["value"] == "manually_pushed_value"
