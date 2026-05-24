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

import os
from datetime import datetime

from airflow.providers.amazon.aws.operators.s3 import S3CreateBucketOperator, S3DeleteBucketOperator
from airflow.providers.amazon.aws.transfers.exasol_to_s3 import ExasolToS3Operator

from tests_common.test_utils.version_compat import AIRFLOW_V_3_0_PLUS

if AIRFLOW_V_3_0_PLUS:
    from airflow.sdk import DAG, Connection, chain, task
else:
    # Airflow 2 path
    from airflow.decorators import task  # type: ignore[attr-defined,no-redef]
    from airflow.models import Connection  # type: ignore[attr-defined,no-redef,assignment]
    from airflow.models.baseoperator import chain  # type: ignore[attr-defined,no-redef]
    from airflow.models.dag import DAG  # type: ignore[attr-defined,no-redef,assignment]

try:
    from airflow.sdk import TriggerRule
except ImportError:
    # Compatibility for Airflow < 3.1
    from airflow.utils.trigger_rule import TriggerRule  # type: ignore[no-redef,attr-defined]

from system.amazon.aws.utils import SystemTestContextBuilder

DAG_ID = "example_exasol_to_s3"

EXASOL_CONNECTION_ID_KEY = "EXASOL_CONNECTION_ID"
EXASOL_HOST_KEY = "EXASOL_HOST"

sys_test_context_task = (
    SystemTestContextBuilder()
    .add_variable(EXASOL_CONNECTION_ID_KEY, default_value="exasol_default")
    .add_variable(EXASOL_HOST_KEY, default_value="host.docker.internal")
    .build()
)


@task
def configure_exasol_connection(connection_id: str, hostname: str):
    c = Connection(
        conn_id=connection_id,
        conn_type="exasol",
        host=hostname,
        port=8563,
        schema="TEST",
        login="SYS",
        password="exasol",
    )

    os.environ[f"AIRFLOW_CONN_{c.conn_id.upper()}"] = c.get_uri()


with DAG(
    dag_id=DAG_ID,
    schedule="@once",
    start_date=datetime(2021, 1, 1),
    catchup=False,
) as dag:
    test_context = sys_test_context_task()
    env_id = test_context["ENV_ID"]
    exasol_connection_id = test_context[EXASOL_CONNECTION_ID_KEY]
    exasol_host = test_context[EXASOL_HOST_KEY]

    s3_bucket = f"{env_id}-exasol-to-s3-bucket"
    s3_key = f"{env_id}/exasol-export.csv"

    create_s3_bucket = S3CreateBucketOperator(task_id="create_s3_bucket", bucket_name=s3_bucket)

    # [START howto_transfer_exasol_to_s3]
    exasol_to_s3_task = ExasolToS3Operator(
        task_id="exasol_to_s3_task",
        exasol_conn_id=exasol_connection_id,
        query_or_table="SELECT 1 AS sample_value",
        bucket_name=s3_bucket,
        key=s3_key,
        replace=True,
    )
    # [END howto_transfer_exasol_to_s3]

    delete_s3_bucket = S3DeleteBucketOperator(
        task_id="delete_s3_bucket",
        bucket_name=s3_bucket,
        force_delete=True,
        trigger_rule=TriggerRule.ALL_DONE,
    )

    chain(
        # TEST SETUP
        test_context,
        configure_exasol_connection(exasol_connection_id, exasol_host),
        create_s3_bucket,
        # TEST BODY
        exasol_to_s3_task,
        # TEST TEARDOWN
        delete_s3_bucket,
    )

    from tests_common.test_utils.watcher import watcher

    # This test needs watcher in order to properly mark success/failure
    # when "tearDown" task with trigger rule is part of the DAG
    list(dag.tasks) >> watcher()

from tests_common.test_utils.system_tests import get_test_run  # noqa: E402

# Needed to run the example DAG with pytest (see: contributing-docs/testing/system_tests.rst)
test_run = get_test_run(dag)
