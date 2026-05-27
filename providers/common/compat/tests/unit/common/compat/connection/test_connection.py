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

import logging
from unittest import mock

import pytest

from airflow.models.connection import Connection
from airflow.providers.common.compat.connection import get_async_connection
from airflow.providers.common.compat.sdk import BaseHook as CompatBaseHook


class MockAgetBaseHook:
    def __init__(*args, **kargs):
        pass

    async def aget_connection(self, conn_id: str):
        return Connection(
            conn_id="test_conn",
            conn_type="http",
            password="secret_token_aget",
        )


class MockBaseHook:
    def __init__(*args, **kargs):
        pass

    def get_connection(self, conn_id: str):
        return Connection(
            conn_id="test_conn_sync",
            conn_type="http",
            password="secret_token",
        )


class TestGetAsyncConnection:
    @mock.patch("airflow.providers.common.compat.connection.BaseHook", new_callable=MockAgetBaseHook)
    @pytest.mark.asyncio
    async def test_get_async_connection_with_aget(self, _, caplog):
        with caplog.at_level(logging.DEBUG):
            conn = await get_async_connection("test_conn")
        assert conn.password == "secret_token_aget"
        assert conn.conn_type == "http"
        assert "Get connection using `hook.aget_connection()." in caplog.text

    @mock.patch("airflow.providers.common.compat.connection.BaseHook", new_callable=MockBaseHook)
    @pytest.mark.asyncio
    async def test_get_async_connection_with_get_connection(self, _, caplog):
        with caplog.at_level(logging.DEBUG):
            conn = await get_async_connection("test_conn")
        assert conn.password == "secret_token"
        assert conn.conn_type == "http"
        assert "Get connection using `hook.get_connection()." in caplog.text

    @pytest.mark.asyncio
    async def test_get_async_connection_uses_hook_override(self):
        class TestHook(MockBaseHook):
            @classmethod
            async def aget_connection(cls, conn_id: str):
                return Connection(
                    conn_id=conn_id,
                    conn_type="http",
                    host="override-host",
                    login="override-login",
                    password="override-password",
                )

        conn = await get_async_connection("test_conn", hook=TestHook())

        assert conn.conn_id == "test_conn"
        assert conn.host == "override-host"
        assert conn.login == "override-login"
        assert conn.password == "override-password"

    @pytest.mark.asyncio
    async def test_get_async_connection_falls_back_to_sync_hook_override(self):
        class TestHook(CompatBaseHook):
            @classmethod
            def get_connection(cls, conn_id: str):
                return Connection(
                    conn_id=conn_id,
                    conn_type="http",
                    host="sync-override-host",
                    login="sync-override-login",
                    password="sync-override-password",
                )

        conn = await get_async_connection("test_conn", hook=TestHook())

        assert conn.conn_id == "test_conn"
        assert conn.host == "sync-override-host"
        assert conn.login == "sync-override-login"
        assert conn.password == "sync-override-password"
