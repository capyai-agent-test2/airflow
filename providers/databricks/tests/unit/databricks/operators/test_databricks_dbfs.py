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

from airflow.providers.databricks.operators.databricks_dbfs import (
    DatabricksDbfsDeleteOperator,
    DatabricksDbfsDownloadOperator,
    DatabricksDbfsGetStatusOperator,
    DatabricksDbfsUploadOperator,
)

TASK_ID = "databricks-dbfs"
DEFAULT_CONN_ID = "databricks_default"


class TestDatabricksDbfsOperators:
    @mock.patch("airflow.providers.databricks.operators.databricks_dbfs.DatabricksDbfsHook")
    def test_upload_operator(self, hook_class):
        operator = DatabricksDbfsUploadOperator(
            task_id=TASK_ID,
            src="/tmp/local.txt",
            dbfs_path="/FileStore/remote.txt",
            overwrite=True,
        )

        result = operator.execute(None)

        assert result == hook_class.return_value.upload_file.return_value
        hook_class.assert_called_once_with(
            DEFAULT_CONN_ID,
            retry_limit=operator.databricks_retry_limit,
            retry_delay=operator.databricks_retry_delay,
            caller="DatabricksDbfsUploadOperator",
        )
        hook_class.return_value.upload_file.assert_called_once_with(
            "/tmp/local.txt", "/FileStore/remote.txt", overwrite=True
        )

    @mock.patch("airflow.providers.databricks.operators.databricks_dbfs.DatabricksDbfsHook")
    def test_download_operator(self, hook_class):
        operator = DatabricksDbfsDownloadOperator(
            task_id=TASK_ID,
            dbfs_path="/FileStore/remote.txt",
            dst="/tmp/local.txt",
            overwrite=True,
        )

        result = operator.execute(None)

        assert result == hook_class.return_value.download_file.return_value
        hook_class.return_value.download_file.assert_called_once_with(
            "/FileStore/remote.txt", "/tmp/local.txt", overwrite=True
        )

    @mock.patch("airflow.providers.databricks.operators.databricks_dbfs.DatabricksDbfsHook")
    def test_get_status_operator(self, hook_class):
        operator = DatabricksDbfsGetStatusOperator(task_id=TASK_ID, dbfs_path="/FileStore/remote.txt")

        result = operator.execute(None)

        assert result == hook_class.return_value.get_status.return_value
        hook_class.return_value.get_status.assert_called_once_with("/FileStore/remote.txt")

    @mock.patch("airflow.providers.databricks.operators.databricks_dbfs.DatabricksDbfsHook")
    def test_delete_operator(self, hook_class):
        operator = DatabricksDbfsDeleteOperator(
            task_id=TASK_ID,
            dbfs_path="/FileStore/remote.txt",
            recursive=True,
        )

        operator.execute(None)

        hook_class.return_value.delete.assert_called_once_with("/FileStore/remote.txt", recursive=True)
