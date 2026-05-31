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

from alembic import context, op
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = "6a2f97c9a1f4"
down_revision = "acc215baed80"
branch_labels = None
depends_on = None
airflow_version = "3.3.0"


def _move_duplicate_dagruns_for_downgrade():
    from airflow.utils.db import AIRFLOW_MOVED_TABLE_PREFIX

    duplicate_ids_query = """
        SELECT id FROM (
            SELECT
                id,
                ROW_NUMBER() OVER (
                    PARTITION BY dag_id, logical_date
                    ORDER BY
                        CASE
                            WHEN run_type = 'scheduled' THEN 0
                            WHEN run_type = 'backfill' THEN 1
                            ELSE 2
                        END,
                        id
                ) AS row_num
            FROM dag_run
            WHERE logical_date IS NOT NULL
        ) duplicate_dag_runs
        WHERE row_num > 1
    """
    conn = op.get_bind()
    offline = context.is_offline_mode()
    if not offline and conn.execute(text(duplicate_ids_query)).fetchone() is None:
        return

    moved_table_name = f"{AIRFLOW_MOVED_TABLE_PREFIX}__3_3_0__duplicate_dag_run"
    if conn.dialect.name == "mysql":
        op.execute(f"CREATE TABLE {moved_table_name} LIKE dag_run")
        op.execute(
            f"INSERT INTO {moved_table_name} SELECT * FROM dag_run WHERE id IN ({duplicate_ids_query})"
        )
    else:
        op.execute(
            f"CREATE TABLE {moved_table_name} AS SELECT * FROM dag_run WHERE id IN ({duplicate_ids_query})"
        )

    if offline:
        op.execute(f"-- TODO: Dag runs unable to be downgraded are moved to {moved_table_name}.")
        op.execute(f"-- TODO: Table {moved_table_name} can be removed after contained data are reviewed.")

    if conn.dialect.name == "mysql":
        op.execute(
            f"""
            DELETE dag_run FROM dag_run
            INNER JOIN ({duplicate_ids_query}) duplicate_dag_runs
                ON dag_run.id = duplicate_dag_runs.id
            """
        )
    else:
        op.execute(f"DELETE FROM dag_run WHERE id IN ({duplicate_ids_query})")


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
    _move_duplicate_dagruns_for_downgrade()
    with op.batch_alter_table("dag_run", schema=None) as batch_op:
        batch_op.drop_constraint("dag_run_dag_id_run_type_logical_date_key", type_="unique")
        batch_op.create_unique_constraint(
            "dag_run_dag_id_logical_date_key",
            columns=["dag_id", "logical_date"],
        )
