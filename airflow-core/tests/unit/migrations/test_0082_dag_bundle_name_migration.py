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

import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations

from tests_common.test_utils.paths import AIRFLOW_CORE_SOURCES_PATH

_MIGRATION_PATH = (
    Path(AIRFLOW_CORE_SOURCES_PATH)
    / "airflow/migrations/versions/0082_3_1_0_make_bundle_name_not_nullable.py"
)
_spec = importlib.util.spec_from_file_location("migration_0082", _MIGRATION_PATH)
_migration = importlib.util.module_from_spec(_spec)  # type: ignore[arg-type]
_spec.loader.exec_module(_migration)  # type: ignore[union-attr]

upgrade = _migration.upgrade

_PRE_0082_DDL = """
CREATE TABLE dag_bundle (
    name VARCHAR(250) PRIMARY KEY
);

CREATE TABLE dag (
    dag_id VARCHAR(250) PRIMARY KEY,
    fileloc VARCHAR(2000) NOT NULL,
    bundle_name VARCHAR(250),
    CONSTRAINT dag_bundle_name_fkey FOREIGN KEY(bundle_name) REFERENCES dag_bundle (name)
);
"""


def _make_engine_pre_0082():
    engine = sa.create_engine("sqlite:///:memory:")
    with engine.begin() as conn:
        for ddl in _PRE_0082_DDL.strip().split(";"):
            conn.execute(sa.text(ddl))
    return engine


def _run_upgrade(engine, bundle_config_list):
    with engine.begin() as conn:
        with Operations.context(MigrationContext.configure(conn)):
            with (
                mock.patch.object(_migration.conf, "getjson", return_value=bundle_config_list),
                mock.patch.object(_migration, "StringID", sa.String),
            ):
                upgrade()


def _read_dags(engine):
    with engine.connect() as conn:
        return conn.execute(sa.text("SELECT dag_id, bundle_name FROM dag ORDER BY dag_id")).all()


def _read_bundle_names(engine):
    with engine.connect() as conn:
        return conn.execute(sa.text("SELECT name FROM dag_bundle ORDER BY name")).scalars().all()


def test_upgrade_uses_configured_bundle_for_existing_dags():
    engine = _make_engine_pre_0082()
    with engine.begin() as conn:
        conn.execute(
            sa.text("INSERT INTO dag (dag_id, fileloc) VALUES (:dag_id, :fileloc)"),
            {"dag_id": "custom_dag", "fileloc": "/files/dags/custom_dag.py"},
        )

    _run_upgrade(
        engine,
        [
            {
                "name": "main",
                "classpath": "airflow.dag_processing.bundles.local.LocalDagBundle",
                "kwargs": {"path": "/files/dags", "refresh_interval": 1},
            }
        ],
    )

    assert _read_dags(engine) == [("custom_dag", "main")]
    assert "main" in _read_bundle_names(engine)


def test_upgrade_uses_matching_configured_bundle_path_before_fallback():
    engine = _make_engine_pre_0082()
    with engine.begin() as conn:
        conn.execute(
            sa.text("INSERT INTO dag (dag_id, fileloc) VALUES (:dag_id, :fileloc)"),
            [
                {"dag_id": "other_dag", "fileloc": "/other/dags/other_dag.py"},
                {"dag_id": "custom_dag", "fileloc": "/files/dags/custom_dag.py"},
                {"dag_id": "fallback_dag", "fileloc": "/unmatched/fallback_dag.py"},
            ],
        )

    _run_upgrade(
        engine,
        [
            {
                "name": "main1",
                "classpath": "airflow.dag_processing.bundles.local.LocalDagBundle",
                "kwargs": {"path": "/other/dags", "refresh_interval": 1},
            },
            {
                "name": "main2",
                "classpath": "airflow.dag_processing.bundles.local.LocalDagBundle",
                "kwargs": {"path": "/files/dags", "refresh_interval": 1},
            },
        ],
    )

    assert _read_dags(engine) == [
        ("custom_dag", "main2"),
        ("fallback_dag", "main1"),
        ("other_dag", "main1"),
    ]
    assert {"main1", "main2"}.issubset(_read_bundle_names(engine))


def test_upgrade_escapes_like_wildcards_in_configured_bundle_paths():
    engine = _make_engine_pre_0082()
    with engine.begin() as conn:
        conn.execute(
            sa.text("INSERT INTO dag (dag_id, fileloc) VALUES (:dag_id, :fileloc)"),
            [
                {"dag_id": "literal_dag", "fileloc": "/files/dags_1!/literal_dag.py"},
                {"dag_id": "wildcard_dag", "fileloc": "/files/dagsX1!/wildcard_dag.py"},
            ],
        )

    _run_upgrade(
        engine,
        [
            {
                "name": "main1",
                "classpath": "airflow.dag_processing.bundles.local.LocalDagBundle",
                "kwargs": {"path": "/fallback/dags", "refresh_interval": 1},
            },
            {
                "name": "main2",
                "classpath": "airflow.dag_processing.bundles.local.LocalDagBundle",
                "kwargs": {"path": "/files/dags_1!", "refresh_interval": 1},
            },
        ],
    )

    assert _read_dags(engine) == [("literal_dag", "main2"), ("wildcard_dag", "main1")]
