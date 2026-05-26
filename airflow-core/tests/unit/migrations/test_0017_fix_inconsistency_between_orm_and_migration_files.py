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

import importlib.util
from pathlib import Path
from unittest import mock

from tests_common.test_utils.paths import AIRFLOW_CORE_SOURCES_PATH

_MIGRATION_PATH = (
    Path(AIRFLOW_CORE_SOURCES_PATH)
    / "airflow/migrations/versions/0017_2_9_2_fix_inconsistency_between_ORM_and_migration_files.py"
)
_spec = importlib.util.spec_from_file_location("migration_0017", _MIGRATION_PATH)
_migration = importlib.util.module_from_spec(_spec)  # type: ignore[arg-type]
_spec.loader.exec_module(_migration)  # type: ignore[union-attr]


class TestDropMysqlUniqueConstraintIfExists:
    def test_drops_existing_constraint(self):
        conn = mock.Mock()
        conn.execute.return_value.scalar.return_value = 1

        _migration.drop_mysql_unique_constraint_if_exists(conn, "connection", "unique_conn_id")

        assert conn.execute.call_count == 2
        lookup_stmt, lookup_params = conn.execute.call_args_list[0].args
        drop_stmt = conn.execute.call_args_list[1].args[0]
        assert "information_schema.TABLE_CONSTRAINTS" in str(lookup_stmt)
        assert lookup_params == {"table_name": "connection", "constraint_name": "unique_conn_id"}
        assert str(drop_stmt) == "ALTER TABLE connection DROP INDEX unique_conn_id"

    def test_skips_missing_constraint(self):
        conn = mock.Mock()
        conn.execute.return_value.scalar.return_value = None

        _migration.drop_mysql_unique_constraint_if_exists(conn, "dag_run", "dag_run_dag_id_run_id_key")

        assert conn.execute.call_count == 1
        lookup_stmt, lookup_params = conn.execute.call_args.args
        assert "information_schema.TABLE_CONSTRAINTS" in str(lookup_stmt)
        assert lookup_params == {
            "table_name": "dag_run",
            "constraint_name": "dag_run_dag_id_run_id_key",
        }
