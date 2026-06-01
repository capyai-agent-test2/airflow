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

import sqlalchemy as sa

from airflow.models.dagrun import DagRun


def _compile_dag_run_schema(dialect: str) -> str:
    statements = []

    def dump(sql, *multiparams, **params):
        statements.append(str(sql.compile(dialect=engine.dialect)))

    engine = sa.create_mock_engine(f"{dialect}://", dump)
    DagRun.__table__.metadata.create_all(engine, tables=[DagRun.__table__])

    return "\n".join(statements)


def test_mysql_schema_does_not_create_duplicate_dag_run_state_dag_id_indexes():
    mysql_schema = _compile_dag_run_schema("mysql")

    assert "idx_dag_run_running_dags" in mysql_schema
    assert "idx_dag_run_queued_dags" not in mysql_schema


def test_sqlite_schema_keeps_partial_dag_run_state_dag_id_indexes():
    sqlite_schema = _compile_dag_run_schema("sqlite")

    assert "idx_dag_run_running_dags" in sqlite_schema
    assert "idx_dag_run_queued_dags" in sqlite_schema
