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
Add dag version cleanup indexes.

Revision ID: b9c8d7e6f5a4
Revises: a1b2c3d4e5f6
Create Date: 2026-05-24 00:00:00.000000
"""

from __future__ import annotations

from alembic import op

revision = "b9c8d7e6f5a4"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None
airflow_version = "3.3.0"


def upgrade():
    """Add indexes that speed up dag_version cleanup."""
    with op.batch_alter_table("task_instance", schema=None) as batch_op:
        batch_op.create_index("idx_task_instance_dag_version_id", ["dag_version_id"], unique=False)

    with op.batch_alter_table("dag_run", schema=None) as batch_op:
        batch_op.create_index("idx_dag_run_created_dag_version_id", ["created_dag_version_id"], unique=False)


def downgrade():
    """Remove indexes that speed up dag_version cleanup."""
    with op.batch_alter_table("task_instance", schema=None) as batch_op:
        batch_op.drop_index("idx_task_instance_dag_version_id")

    with op.batch_alter_table("dag_run", schema=None) as batch_op:
        batch_op.drop_index("idx_dag_run_created_dag_version_id")
