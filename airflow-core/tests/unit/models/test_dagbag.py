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

import time
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import MagicMock, patch

import pytest
import time_machine
from cachetools import LRUCache, TTLCache

from airflow.models.dagbag import DBDagBag
from airflow.models.serialized_dag import SerializedDagModel
from airflow.providers.standard.operators.empty import EmptyOperator
from airflow.serialization.serialized_objects import LazyDeserializedDAG, SerializedDAG

pytestmark = pytest.mark.db_test

# This file previously contained tests for DagBag functionality, but those tests
# have been moved to airflow-core/tests/unit/dag_processing/test_dagbag.py to match
# the source code reorganization where DagBag moved from models to dag_processing.
#
# Tests for models-specific functionality (DBDagBag, DagPriorityParsingRequest, etc.)
# remain in this file.


class TestDBDagBag:
    def setup_method(self):
        self.db_dag_bag = DBDagBag()
        self.session = MagicMock()

    def test__read_dag_stores_and_returns_dag(self):
        """It should return the SerializedDAG without caching by default."""
        mock_dag = MagicMock(spec=SerializedDAG)
        mock_serdag = MagicMock(spec=SerializedDagModel)
        mock_serdag.dag = mock_dag
        mock_serdag.dag_version_id = "v1"

        result = self.db_dag_bag._read_dag(mock_serdag)

        assert result == mock_dag
        assert "v1" not in self.db_dag_bag._dags
        assert mock_serdag.load_op_links is True

    def test__read_dag_returns_none_when_no_dag(self):
        """It should return None and not modify _dags when no DAG is present."""
        mock_serdag = MagicMock(spec=SerializedDagModel)
        mock_serdag.dag = None
        mock_serdag.dag_version_id = "v1"

        result = self.db_dag_bag._read_dag(mock_serdag)

        assert result is None
        assert "v1" not in self.db_dag_bag._dags

    def test_get_dag_fetches_from_db_on_miss(self):
        """It should query the DB and cache the result when not in cache."""
        mock_dag = MagicMock(spec=SerializedDAG)
        mock_serdag = MagicMock(spec=SerializedDagModel)
        mock_serdag.dag = mock_dag
        mock_serdag.dag_version_id = "v1"
        self.session.scalar.return_value = mock_serdag

        result = self.db_dag_bag.get_dag("v1", session=self.session)

        self.session.scalar.assert_called_once()
        assert result == mock_dag

    def test_get_dag_queries_db_again_when_caching_disabled(self):
        """It should query the DB on repeat lookups when caching is disabled."""
        mock_dag = MagicMock(spec=SerializedDAG)
        mock_serdag = MagicMock(spec=SerializedDagModel)
        mock_serdag.dag = mock_dag
        mock_serdag.dag_version_id = "v1"
        self.session.scalar.return_value = mock_serdag

        first = self.db_dag_bag.get_dag("v1", session=self.session)
        second = self.db_dag_bag.get_dag("v1", session=self.session)

        assert first == mock_dag
        assert second == mock_dag
        assert self.session.scalar.call_count == 2

    def test_get_dag_returns_none_when_not_found(self):
        """It should return None if version_id not found in DB."""
        self.session.scalar.return_value = None

        result = self.db_dag_bag.get_dag("v1", session=self.session)

        assert result is None


class TestDBDagBagCache:
    """Tests for DBDagBag optional caching behavior."""

    def test_no_caching_by_default(self):
        """Test that DBDagBag uses a simple dict without caching by default."""
        dag_bag = DBDagBag()
        assert dag_bag._use_cache is False
        assert isinstance(dag_bag._dags, dict)

    def test_lru_cache_enabled_with_cache_size(self):
        """Test that LRU cache is enabled when cache_size is provided."""
        dag_bag = DBDagBag(cache_size=10)
        assert dag_bag._use_cache is True
        assert isinstance(dag_bag._dags, LRUCache)

    def test_ttl_cache_enabled_with_cache_size_and_ttl(self):
        """Test that TTL cache is enabled when both cache_size and cache_ttl are provided."""
        dag_bag = DBDagBag(cache_size=10, cache_ttl=60)
        assert dag_bag._use_cache is True
        assert isinstance(dag_bag._dags, TTLCache)

    def test_zero_cache_size_disables_caching(self):
        """Test that cache_size=0 disables caching."""
        dag_bag = DBDagBag(cache_size=0, cache_ttl=60)
        assert dag_bag._use_cache is False
        assert isinstance(dag_bag._dags, dict)

    def test_clear_cache_with_caching(self):
        """Test clear_cache() with caching enabled."""
        dag_bag = DBDagBag(cache_size=10, cache_ttl=60)

        mock_dag = MagicMock()
        dag_bag._dags["version_1"] = mock_dag
        dag_bag._dags["version_2"] = mock_dag
        assert len(dag_bag._dags) == 2

        count = dag_bag.clear_cache()
        assert count == 2
        assert len(dag_bag._dags) == 0

    def test_clear_cache_without_caching(self):
        """Test clear_cache() without caching enabled."""
        dag_bag = DBDagBag()

        mock_dag = MagicMock()
        dag_bag._dags["version_1"] = mock_dag
        dag_bag._dag_last_updated["version_1"] = MagicMock()
        assert len(dag_bag._dags) == 1

        count = dag_bag.clear_cache()
        assert count == 1
        assert len(dag_bag._dags) == 0
        assert len(dag_bag._dag_last_updated) == 0

    def test_ttl_cache_expiry(self):
        """Test that cached DAGs expire after TTL."""
        # TTLCache defaults to time.monotonic which time_machine cannot control.
        # Use time.time as the timer so time_machine can advance it.
        dag_bag = DBDagBag(cache_size=10, cache_ttl=1)
        dag_bag._dags = TTLCache(maxsize=10, ttl=1, timer=time.time)

        with time_machine.travel("2025-01-01 00:00:00", tick=False):
            dag_bag._dags["test_version_id"] = MagicMock()
            assert "test_version_id" in dag_bag._dags

        # Jump ahead beyond TTL
        with time_machine.travel("2025-01-01 00:00:02", tick=False):
            assert dag_bag._dags.get("test_version_id") is None

    def test_lru_eviction(self):
        """Test that LRU eviction works when cache is full."""
        dag_bag = DBDagBag(cache_size=2)

        dag_bag._dags["version_1"] = MagicMock()
        dag_bag._dags["version_2"] = MagicMock()
        dag_bag._dags["version_3"] = MagicMock()

        # version_1 should be evicted (LRU)
        assert dag_bag._dags.get("version_1") is None
        assert dag_bag._dags.get("version_2") is not None
        assert dag_bag._dags.get("version_3") is not None

    def test_thread_safety_with_caching(self):
        """Test concurrent access doesn't cause race conditions with caching enabled."""
        dag_bag = DBDagBag(cache_size=100, cache_ttl=60)
        errors = []
        mock_session = MagicMock()

        def make_dag_version(version_id):
            serdag = MagicMock()
            serdag.dag = MagicMock()
            serdag.dag_version_id = version_id
            return MagicMock(serialized_dag=serdag)

        def get_dag_version(model, version_id, options=None, **kwargs):
            return make_dag_version(version_id)

        mock_session.get.side_effect = get_dag_version

        def access_cache(i):
            try:
                dag_bag._get_dag(f"version_{i % 5}", mock_session)
            except Exception as e:
                errors.append(e)

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(access_cache, i) for i in range(100)]
            for f in futures:
                f.result()

        assert not errors

    def test_read_dag_stores_in_bounded_cache(self):
        """Test that _read_dag stores DAG in bounded cache when cache_size > 0."""
        dag_bag = DBDagBag(cache_size=10, cache_ttl=60)

        mock_sdm = MagicMock()
        mock_sdm.dag = MagicMock()
        mock_sdm.dag_version_id = "test_version"

        result = dag_bag._read_dag(mock_sdm)

        assert result == mock_sdm.dag
        assert "test_version" in dag_bag._dags

    def test_read_dag_does_not_store_without_cache(self):
        """Test that _read_dag skips caching when no cache_size is configured."""
        dag_bag = DBDagBag()

        mock_sdm = MagicMock()
        mock_sdm.dag = MagicMock()
        mock_sdm.dag_version_id = "test_version"

        result = dag_bag._read_dag(mock_sdm)

        assert result == mock_sdm.dag
        assert "test_version" not in dag_bag._dags

    def test_iter_all_latest_version_dags_does_not_cache(self):
        """Test that iter_all_latest_version_dags does not cache to prevent thrashing."""
        dag_bag = DBDagBag(cache_size=10, cache_ttl=60)

        mock_session = MagicMock()
        mock_sdm = MagicMock()
        mock_sdm.dag = MagicMock()
        mock_sdm.dag_version_id = "test_version"
        mock_session.scalars.return_value = [mock_sdm]

        list(dag_bag.iter_all_latest_version_dags(session=mock_session))

        # Cache should be empty -- iter doesn't cache to prevent thrashing
        assert len(dag_bag._dags) == 0

    @patch("airflow.models.dagbag.stats")
    def test_cache_hit_metric_emitted(self, mock_stats):
        """Test that cache hit metric is emitted when caching is enabled."""
        dag_bag = DBDagBag(cache_size=10, cache_ttl=60)
        mock_session = MagicMock()
        dag_bag._dags["test_version"] = MagicMock()
        dag_bag._dag_last_updated["test_version"] = "updated"
        mock_session.scalar.return_value = "updated"

        dag_bag._get_dag("test_version", mock_session)

        mock_stats.incr.assert_called_with("api_server.dag_bag.cache_hit")

    @patch("airflow.models.dagbag.stats")
    def test_cache_miss_metric_emitted(self, mock_stats):
        """Test that cache miss metric is emitted when DAG is found in DB but not in cache."""
        dag_bag = DBDagBag(cache_size=10, cache_ttl=60)
        mock_session = MagicMock()

        # Set up a DB result so _get_dag reaches the miss metric path
        mock_serdag = MagicMock(spec=SerializedDagModel)
        mock_serdag.dag = MagicMock(spec=SerializedDAG)
        mock_serdag.dag_version_id = "uncached_version"
        mock_session.scalar.return_value = mock_serdag

        dag_bag._get_dag("uncached_version", mock_session)

        mock_stats.incr.assert_any_call("api_server.dag_bag.cache_miss")

    @patch("airflow.models.dagbag.stats")
    def test_stale_cached_dag_is_refreshed(self, mock_stats):
        """Test that a cached DAG is refreshed when the serialized row changes in place."""
        dag_bag = DBDagBag(cache_size=10, cache_ttl=60)
        mock_session = MagicMock()
        stale_dag = MagicMock(spec=SerializedDAG)
        fresh_dag = MagicMock(spec=SerializedDAG)
        dag_bag._dags["version_1"] = stale_dag
        dag_bag._dag_last_updated["version_1"] = "old"

        mock_serdag = MagicMock(spec=SerializedDagModel)
        mock_serdag.dag = fresh_dag
        mock_serdag.dag_version_id = "version_1"
        mock_serdag.last_updated = "new"
        mock_session.scalar.side_effect = ["new", mock_serdag]

        result = dag_bag._get_dag("version_1", mock_session)

        assert result is fresh_dag
        assert dag_bag._dags["version_1"] is fresh_dag
        assert dag_bag._dag_last_updated["version_1"] == "new"
        mock_stats.incr.assert_any_call("api_server.dag_bag.cache_miss")

    @patch("airflow.models.dagbag.stats")
    def test_cache_clear_metric_emitted(self, mock_stats):
        """Test that cache clear metric is emitted when caching is enabled."""
        dag_bag = DBDagBag(cache_size=10, cache_ttl=60)
        dag_bag._dags["test_version"] = MagicMock()

        dag_bag.clear_cache()

        mock_stats.incr.assert_called_with("api_server.dag_bag.cache_clear")

    @patch("airflow.models.dagbag.stats")
    def test_cache_size_gauge_emitted(self, mock_stats):
        """Test that cache size gauge is emitted when a DAG is cached."""
        dag_bag = DBDagBag(cache_size=10, cache_ttl=60)
        mock_serdag = MagicMock()
        mock_serdag.dag_version_id = "test_version_1"
        mock_serdag.dag = MagicMock()
        mock_serdag.load_op_links = True

        dag_bag._read_dag(mock_serdag)

        mock_stats.gauge.assert_called_with("api_server.dag_bag.cache_size", 1, rate=0.1)

    def test_default_dag_bag_reloads_in_place_serialized_updates(self, dag_maker, session):
        """Test that default DBDagBag sees in-place serialized DAG updates."""
        with dag_maker(dag_id="test_in_place_update", session=session) as dag:
            EmptyOperator(task_id="task_1")

        SerializedDagModel.write_dag(
            dag=LazyDeserializedDAG.from_dag(dag),
            bundle_name="test_bundle",
            bundle_version=None,
            session=session,
        )
        session.commit()

        dag_version = SerializedDagModel.get("test_in_place_update", session=session).dag_version_id
        dag_bag = DBDagBag()

        initial_dag = dag_bag.get_dag(dag_version, session=session)
        assert initial_dag is not None
        assert set(initial_dag.task_dict) == {"task_1"}

        EmptyOperator(task_id="task_2", dag=dag)
        SerializedDagModel.write_dag(
            dag=LazyDeserializedDAG.from_dag(dag),
            bundle_name="test_bundle",
            bundle_version=None,
            session=session,
        )
        session.commit()

        updated_dag = dag_bag.get_dag(dag_version, session=session)
        assert updated_dag is not None
        assert set(updated_dag.task_dict) == {"task_1", "task_2"}
