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

import base64
import json
from unittest import mock

import pytest

from airflow.models import Connection
from airflow.providers.common.compat.sdk import AirflowException
from airflow.providers.databricks.hooks.databricks_dbfs import DatabricksDbfsHook

DEFAULT_CONN_ID = "databricks_default"
HOST = "xx.cloud.databricks.com"
TOKEN = "token"


class TestDatabricksDbfsHook:
    @pytest.fixture(autouse=True)
    def setup_connections(self, create_connection_without_db):
        create_connection_without_db(
            Connection(
                conn_id=DEFAULT_CONN_ID,
                conn_type="databricks",
                host=HOST,
                login=None,
                password=None,
                extra=json.dumps({"token": TOKEN}),
                schema="https",
            )
        )
        self.hook = DatabricksDbfsHook()

    @mock.patch("airflow.providers.databricks.hooks.databricks_dbfs.requests.post")
    def test_upload_file(self, mock_post, tmp_path):
        local_file = tmp_path / "upload.txt"
        local_file.write_text("payload")
        mock_post.return_value.raise_for_status.return_value = None

        result = self.hook.upload_file(str(local_file), "/FileStore/upload.txt", overwrite=True)

        assert result == "/FileStore/upload.txt"
        mock_post.assert_called_once()
        assert mock_post.call_args.args == (f"https://{HOST}/api/2.0/dbfs/put",)
        assert mock_post.call_args.kwargs["data"] == {
            "path": "/FileStore/upload.txt",
            "overwrite": "true",
        }
        assert mock_post.call_args.kwargs["files"]["contents"][0] == "upload.txt"

    def test_download_file(self, tmp_path):
        destination = tmp_path / "nested" / "download.txt"
        self.hook.get_status = mock.Mock(return_value={"is_dir": False, "file_size": 11})
        self.hook.read = mock.Mock(
            side_effect=[
                {"bytes_read": 6, "data": base64.b64encode(b"hello ").decode()},
                {"bytes_read": 5, "data": base64.b64encode(b"world").decode()},
            ]
        )

        result = self.hook.download_file("/FileStore/download.txt", str(destination), chunk_size=6)

        assert result == str(destination)
        assert destination.read_bytes() == b"hello world"
        assert self.hook.read.call_args_list == [
            mock.call("/FileStore/download.txt", offset=0, length=6),
            mock.call("/FileStore/download.txt", offset=6, length=5),
        ]

    def test_download_file_existing_destination_requires_overwrite(self, tmp_path):
        destination = tmp_path / "download.txt"
        destination.write_text("existing")

        with pytest.raises(AirflowException, match="Local file already exists"):
            self.hook.download_file("/FileStore/download.txt", str(destination))

    @pytest.mark.asyncio
    @mock.patch("airflow.providers.databricks.hooks.databricks_base.aiohttp.ClientSession.put")
    async def test_async_base_hook_supports_put(self, mock_put):
        response = mock_put.return_value.__aenter__.return_value
        response.json = mock.AsyncMock(return_value={"ok": True})
        async with self.hook:
            result = await self.hook._a_do_api_call(("PUT", "2.0/dbfs/example"), {"foo": "bar"})

        assert result == {"ok": True}
        mock_put.assert_called_once()

    @mock.patch("airflow.providers.databricks.hooks.databricks_base.requests.put")
    def test_base_hook_supports_put(self, mock_put):
        mock_put.return_value.json.return_value = {"ok": True}

        result = self.hook._do_api_call(("PUT", "2.0/dbfs/example"), {"foo": "bar"})

        assert result == {"ok": True}
        mock_put.assert_called_once()
