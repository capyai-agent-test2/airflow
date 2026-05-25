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

from airflow.providers.common.compat.sdk import AirflowException
from airflow.providers.databricks.operators.databricks_sql import (
    DatabricksSqlWarehouseCreateOperator,
    DatabricksSqlWarehouseDeleteOperator,
    DatabricksSqlWarehouseStartOperator,
    DatabricksSqlWarehouseStopOperator,
)

TASK_ID = "databricks-sql-warehouse-operator"
DEFAULT_CONN_ID = "databricks_default"
WAREHOUSE_ID = "warehouse-id"


@mock.patch("airflow.providers.databricks.operators.databricks_sql.DatabricksHook")
def test_create_sql_warehouse_operator(db_mock_class):
    op = DatabricksSqlWarehouseCreateOperator(
        task_id=TASK_ID,
        name="warehouse",
        cluster_size="2X-Small",
    )
    db_mock = db_mock_class.return_value
    db_mock.create_sql_warehouse.return_value = WAREHOUSE_ID

    result = op.execute(None)

    assert result == WAREHOUSE_ID
    db_mock_class.assert_called_once_with(
        DEFAULT_CONN_ID,
        retry_limit=op.databricks_retry_limit,
        retry_delay=op.databricks_retry_delay,
        caller="DatabricksSqlWarehouseCreateOperator",
    )
    db_mock.create_sql_warehouse.assert_called_once_with({"name": "warehouse", "cluster_size": "2X-Small"})


@pytest.mark.parametrize(
    ("operator_class", "hook_method"),
    [
        pytest.param(DatabricksSqlWarehouseDeleteOperator, "delete_sql_warehouse", id="delete"),
        pytest.param(DatabricksSqlWarehouseStartOperator, "start_sql_warehouse", id="start"),
        pytest.param(DatabricksSqlWarehouseStopOperator, "stop_sql_warehouse", id="stop"),
    ],
)
@mock.patch("airflow.providers.databricks.operators.databricks_sql.DatabricksHook")
def test_sql_warehouse_lifecycle_operators(db_mock_class, operator_class, hook_method):
    op = operator_class(task_id=TASK_ID, warehouse_id=WAREHOUSE_ID)
    db_mock = db_mock_class.return_value

    op.execute(None)

    db_mock_class.assert_called_once_with(
        DEFAULT_CONN_ID,
        retry_limit=op.databricks_retry_limit,
        retry_delay=op.databricks_retry_delay,
        caller=operator_class.__name__,
    )
    getattr(db_mock, hook_method).assert_called_once_with(WAREHOUSE_ID)


def test_create_sql_warehouse_requires_name():
    op = DatabricksSqlWarehouseCreateOperator(task_id=TASK_ID, cluster_size="2X-Small")

    with pytest.raises(AirflowException, match="Missing required parameter: name"):
        op.execute(None)


def test_create_sql_warehouse_requires_cluster_size():
    op = DatabricksSqlWarehouseCreateOperator(task_id=TASK_ID, name="warehouse")

    with pytest.raises(AirflowException, match="Missing required parameter: cluster_size"):
        op.execute(None)
