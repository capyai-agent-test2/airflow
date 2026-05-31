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
Allow manual and scheduled runs with same logical date.

Revision ID: 6a2f97c9a1f4
Revises: acc215baed80
Create Date: 2026-05-31 00:00:00.000000
"""

from __future__ import annotations

from alembic import op

# revision identifiers, used by Alembic.
revision = "6a2f97c9a1f4"
down_revision = "acc215baed80"
branch_labels = None
depends_on = None
airflow_version = "3.3.0"


def upgrade():
    """Allow different Dag run types to share logical dates."""
    with op.batch_alter_table("dag_run", schema=None) as batch_op:
        batch_op.drop_constraint("dag_run_dag_id_logical_date_key", type_="unique")
        batch_op.create_unique_constraint(
            "dag_run_dag_id_run_type_logical_date_key",
            columns=["dag_id", "run_type", "logical_date"],
        )


def downgrade():
    """Restore uniqueness of Dag logical dates."""
    with op.batch_alter_table("dag_run", schema=None) as batch_op:
        batch_op.drop_constraint("dag_run_dag_id_run_type_logical_date_key", type_="unique")
        batch_op.create_unique_constraint(
            "dag_run_dag_id_logical_date_key",
            columns=["dag_id", "logical_date"],
        )
