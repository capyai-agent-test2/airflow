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

from unittest.mock import create_autospec

from sqlalchemy.orm import Session

from airflow.models.connection import Connection
from airflow.models.pool import Pool
from airflow.utils.db import add_default_pool_if_not_exists, merge_conn


class TestProvideSessionCommitBehavior:
    def test_merge_conn_does_not_commit_provided_session(self):
        session = create_autospec(Session, instance=True)
        session.scalar.return_value = None

        merge_conn(Connection(conn_id="test-conn"), session=session)

        session.add.assert_called_once()
        session.commit.assert_not_called()

    def test_add_default_pool_does_not_commit_provided_session(self):
        session = create_autospec(Session, instance=True)
        session.scalar.return_value = None

        add_default_pool_if_not_exists(session=session)

        session.add.assert_called_once()
        added_pool = session.add.call_args.args[0]
        assert isinstance(added_pool, Pool)
        assert added_pool.pool == Pool.DEFAULT_POOL_NAME
        session.commit.assert_not_called()

    def test_merge_conn_commits_when_decorator_creates_session(self, monkeypatch):
        session = create_autospec(Session, instance=True)
        session.scalar.return_value = None

        def fake_create_session(scoped: bool = True):
            assert scoped is True

            class _Context:
                def __enter__(self_inner):
                    return session

                def __exit__(self_inner, exc_type, exc, tb):
                    if exc_type is None:
                        session.commit()
                    else:
                        session.rollback()

            return _Context()

        monkeypatch.setattr("airflow.utils.session.create_session", fake_create_session)

        merge_conn(Connection(conn_id="test-conn"))

        session.add.assert_called_once()
        session.commit.assert_called_once()

    def test_add_default_pool_commits_when_decorator_creates_session(self, monkeypatch):
        session = create_autospec(Session, instance=True)
        session.scalar.return_value = None

        def fake_create_session(scoped: bool = True):
            assert scoped is True

            class _Context:
                def __enter__(self_inner):
                    return session

                def __exit__(self_inner, exc_type, exc, tb):
                    if exc_type is None:
                        session.commit()
                    else:
                        session.rollback()

            return _Context()

        monkeypatch.setattr("airflow.utils.session.create_session", fake_create_session)

        add_default_pool_if_not_exists()

        session.add.assert_called_once()
        session.commit.assert_called_once()
