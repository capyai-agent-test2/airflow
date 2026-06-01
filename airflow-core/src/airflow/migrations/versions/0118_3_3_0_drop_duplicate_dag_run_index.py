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

"""
Drop duplicate Dag run index on MySQL.

Revision ID: f2a2349c5a7d
Revises: 8812eb67b63c
Create Date: 2026-06-01 00:00:00.000000

"""

from __future__ import annotations

from alembic import op

# revision identifiers, used by Alembic.
revision = "f2a2349c5a7d"
down_revision = "8812eb67b63c"
branch_labels = None
depends_on = None
airflow_version = "3.3.0"


def upgrade():
    """Drop duplicate Dag run index on MySQL."""
    if op.get_bind().dialect.name == "mysql":
        with op.batch_alter_table("dag_run") as batch_op:
            batch_op.drop_index("idx_dag_run_queued_dags", if_exists=True)


def downgrade():
    """Restore duplicate Dag run index on MySQL."""
    if op.get_bind().dialect.name == "mysql":
        with op.batch_alter_table("dag_run") as batch_op:
            batch_op.create_index("idx_dag_run_queued_dags", ["state", "dag_id"], if_not_exists=True)
