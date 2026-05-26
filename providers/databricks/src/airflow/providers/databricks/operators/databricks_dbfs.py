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
"""Operators for interacting with Databricks DBFS."""

from __future__ import annotations

from collections.abc import Sequence
from functools import cached_property
from typing import TYPE_CHECKING, Any

from airflow.providers.common.compat.sdk import BaseOperator
from airflow.providers.databricks.hooks.databricks_dbfs import DatabricksDbfsHook

if TYPE_CHECKING:
    from airflow.providers.common.compat.sdk import Context


class _DatabricksDbfsOperator(BaseOperator):
    """Base class for Databricks DBFS operators."""

    template_fields: Sequence[str] = ("databricks_conn_id",)

    def __init__(
        self,
        *,
        databricks_conn_id: str = "databricks_default",
        databricks_retry_limit: int = 3,
        databricks_retry_delay: int = 1,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.databricks_conn_id = databricks_conn_id
        self.databricks_retry_limit = databricks_retry_limit
        self.databricks_retry_delay = databricks_retry_delay

    @cached_property
    def _hook(self) -> DatabricksDbfsHook:
        return DatabricksDbfsHook(
            self.databricks_conn_id,
            retry_limit=self.databricks_retry_limit,
            retry_delay=self.databricks_retry_delay,
            caller=self.__class__.__name__,
        )


class DatabricksDbfsUploadOperator(_DatabricksDbfsOperator):
    """Upload a local file to DBFS."""

    template_fields: Sequence[str] = ("src", "dbfs_path", "databricks_conn_id")

    def __init__(self, *, src: str, dbfs_path: str, overwrite: bool = False, **kwargs) -> None:
        super().__init__(**kwargs)
        self.src = src
        self.dbfs_path = dbfs_path
        self.overwrite = overwrite

    def execute(self, context: Context) -> str:
        return self._hook.upload_file(self.src, self.dbfs_path, overwrite=self.overwrite)


class DatabricksDbfsDownloadOperator(_DatabricksDbfsOperator):
    """Download a DBFS file to the local filesystem."""

    template_fields: Sequence[str] = ("dbfs_path", "dst", "databricks_conn_id")

    def __init__(self, *, dbfs_path: str, dst: str, overwrite: bool = False, **kwargs) -> None:
        super().__init__(**kwargs)
        self.dbfs_path = dbfs_path
        self.dst = dst
        self.overwrite = overwrite

    def execute(self, context: Context) -> str:
        return self._hook.download_file(self.dbfs_path, self.dst, overwrite=self.overwrite)


class DatabricksDbfsGetStatusOperator(_DatabricksDbfsOperator):
    """Fetch metadata for a DBFS file or directory."""

    template_fields: Sequence[str] = ("dbfs_path", "databricks_conn_id")

    def __init__(self, *, dbfs_path: str, **kwargs) -> None:
        super().__init__(**kwargs)
        self.dbfs_path = dbfs_path

    def execute(self, context: Context) -> dict[str, Any]:
        return self._hook.get_status(self.dbfs_path)


class DatabricksDbfsDeleteOperator(_DatabricksDbfsOperator):
    """Delete a DBFS file or directory."""

    template_fields: Sequence[str] = ("dbfs_path", "databricks_conn_id")

    def __init__(self, *, dbfs_path: str, recursive: bool = False, **kwargs) -> None:
        super().__init__(**kwargs)
        self.dbfs_path = dbfs_path
        self.recursive = recursive

    def execute(self, context: Context) -> None:
        self._hook.delete(self.dbfs_path, recursive=self.recursive)
