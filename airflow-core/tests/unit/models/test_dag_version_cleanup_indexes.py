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

from sqlalchemy import inspect

from airflow.models.dagrun import DagRun
from airflow.models.taskinstance import TaskInstance


def test_task_instance_defines_index_for_dag_version_cleanup():
    index_columns = {
        index.name: tuple(column.name for column in index.columns) for index in TaskInstance.__table__.indexes
    }

    assert index_columns["idx_task_instance_dag_version_id"] == ("dag_version_id",)


def test_dag_run_defines_index_for_dag_version_cleanup():
    index_columns = {
        index.name: tuple(column.name for column in index.columns) for index in DagRun.__table__.indexes
    }

    assert index_columns["idx_dag_run_created_dag_version_id"] == ("created_dag_version_id",)


def test_db_migration_creates_dag_version_cleanup_indexes(session):
    inspector = inspect(session.get_bind())
    task_instance_indexes = {index["name"] for index in inspector.get_indexes("task_instance")}
    dag_run_indexes = {index["name"] for index in inspector.get_indexes("dag_run")}

    assert "idx_task_instance_dag_version_id" in task_instance_indexes
    assert "idx_dag_run_created_dag_version_id" in dag_run_indexes
