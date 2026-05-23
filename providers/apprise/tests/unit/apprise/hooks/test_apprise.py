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

import json
from pathlib import Path
from unittest import mock
from unittest.mock import AsyncMock, MagicMock, call, patch

import apprise
import pytest
from apprise import NotifyFormat, NotifyType

from airflow.models import Connection
from airflow.providers.apprise.hooks.apprise import AppriseHook


class TestAppriseHook:
    """
    Test for AppriseHook
    """

    @pytest.mark.parametrize(
        "config",
        [
            {"path": "http://some_path_that_dont_exist/", "tag": "alert"},
            '{"path": "http://some_path_that_dont_exist/", "tag": "alert"}',
        ],
    )
    def test_get_config_from_conn(self, config):
        extra = {"config": config}
        conn = Connection(conn_type="apprise", extra=extra)
        hook = AppriseHook()
        assert hook.get_config_from_conn(conn) == (json.loads(config) if isinstance(config, str) else config)

    def test_set_config_from_conn_with_dict(self):
        """
        Test set_config_from_conn for dict config
        """
        extra = {"config": {"path": "http://some_path_that_dont_exist/", "tag": "alert"}}
        apprise_obj = apprise.Apprise()
        apprise_obj.add = MagicMock()
        conn = Connection(conn_type="apprise", extra=extra)
        hook = AppriseHook()
        hook.set_config_from_conn(conn=conn, apprise_obj=apprise_obj)

        apprise_obj.add.assert_called_once_with("http://some_path_that_dont_exist/", tag="alert")

    def test_set_config_from_conn_with_list(self):
        """
        Test set_config_from_conn for list of dict config
        """
        extra = {
            "config": [
                {"path": "http://some_path_that_dont_exist/", "tag": "p0"},
                {"path": "http://some_other_path_that_dont_exist/", "tag": "p1"},
            ]
        }

        apprise_obj = apprise.Apprise()
        apprise_obj.add = MagicMock()
        conn = Connection(conn_type="apprise", extra=extra)
        hook = AppriseHook()
        hook.set_config_from_conn(conn=conn, apprise_obj=apprise_obj)

        apprise_obj.add.assert_has_calls(
            [
                call("http://some_path_that_dont_exist/", tag="p0"),
                call("http://some_other_path_that_dont_exist/", tag="p1"),
            ]
        )

    def test_get_storage_path_uses_default_temp_dir(self, monkeypatch):
        monkeypatch.delenv("APPRISE_STORAGE_PATH", raising=False)

        hook = AppriseHook()

        assert hook.get_storage_path().endswith("/apprise_cache")

    def test_build_apprise_obj_enables_persistent_storage(self, monkeypatch, tmp_path):
        monkeypatch.setenv("APPRISE_STORAGE_PATH", str(tmp_path))
        asset = object()
        apprise_obj = apprise.Apprise()
        with (
            patch.object(apprise, "AppriseAsset", return_value=asset) as mock_asset,
            patch.object(apprise, "Apprise", return_value=apprise_obj) as mock_apprise,
        ):
            hook = AppriseHook()
            result = hook.build_apprise_obj()

        assert result is apprise_obj
        assert Path(tmp_path).is_dir()
        mock_asset.assert_called_once_with(
            storage_path=str(tmp_path), storage_mode=apprise.PersistentStoreMode.AUTO
        )
        mock_apprise.assert_called_once_with(asset=asset)

    def test_build_apprise_obj_falls_back_when_persistent_storage_is_unavailable(self):
        apprise_obj = apprise.Apprise()
        with (
            patch.object(apprise, "PersistentStoreMode", None, create=True),
            patch.object(apprise, "AppriseAsset", None, create=True),
            patch.object(apprise, "Apprise", return_value=apprise_obj) as mock_apprise,
        ):
            hook = AppriseHook()
            result = hook.build_apprise_obj()

        assert result is apprise_obj
        mock_apprise.assert_called_once_with()

    @mock.patch(
        "airflow.providers.apprise.hooks.apprise.AppriseHook.get_connection",
    )
    def test_notify(self, mock_conn):
        mock_conn.return_value = Connection(
            conn_id="apprise",
            extra={
                "config": [
                    {"path": "http://some_path_that_dont_exist/", "tag": "p0"},
                    {"path": "http://some_other_path_that_dont_exist/", "tag": "p1"},
                ]
            },
        )
        apprise_obj = apprise.Apprise()
        apprise_obj.notify = MagicMock()
        apprise_obj.add = MagicMock()
        with patch.object(AppriseHook, "build_apprise_obj", return_value=apprise_obj):
            hook = AppriseHook()
            hook.notify(body="test")

        apprise_obj.notify.assert_called_once_with(
            body="test",
            title="",
            notify_type=NotifyType.INFO,
            body_format=NotifyFormat.TEXT,
            tag="all",
            attach=None,
            interpret_escapes=None,
        )

    @pytest.mark.asyncio
    @mock.patch(
        "airflow.providers.apprise.hooks.apprise.get_async_connection",
    )
    async def test_async_notify(self, mock_conn):
        mock_conn.return_value = Connection(
            conn_id="apprise",
            extra={
                "config": [
                    {"path": "http://some_path_that_dont_exist/", "tag": "p0"},
                    {"path": "http://some_other_path_that_dont_exist/", "tag": "p1"},
                ]
            },
        )
        apprise_obj = apprise.Apprise()
        apprise_obj.async_notify = AsyncMock()
        apprise_obj.add = MagicMock()
        with patch.object(AppriseHook, "build_apprise_obj", return_value=apprise_obj):
            hook = AppriseHook()
            await hook.async_notify(body="test")

        mock_conn.assert_called()
        apprise_obj.async_notify.assert_called_once_with(
            body="test",
            title="",
            notify_type=NotifyType.INFO,
            body_format=NotifyFormat.TEXT,
            tag="all",
            attach=None,
            interpret_escapes=None,
        )
