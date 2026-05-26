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
"""Hook for interacting with the Databricks DBFS API."""

from __future__ import annotations

from base64 import b64decode
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

import requests
from requests import exceptions as requests_exceptions
from requests.auth import HTTPBasicAuth
from tenacity import RetryError

from airflow.providers.common.compat.sdk import AirflowException
from airflow.providers.databricks.hooks.databricks_base import BaseDatabricksHook, _TokenAuth

DBFS_GET_STATUS_ENDPOINT = ("GET", "2.0/dbfs/get-status")
DBFS_READ_ENDPOINT = ("GET", "2.0/dbfs/read")
DBFS_DELETE_ENDPOINT = ("POST", "2.0/dbfs/delete")
DBFS_PUT_ENDPOINT = ("POST", "2.0/dbfs/put")


class DatabricksDbfsHook(BaseDatabricksHook):
    """Interact with Databricks DBFS endpoints."""

    conn_name_attr = "databricks_conn_id"
    default_conn_name = "databricks_default"
    conn_type = "databricks"
    hook_name = "Databricks"

    def get_status(self, dbfs_path: str) -> dict[str, Any]:
        """Get file or directory metadata from DBFS."""
        return self._do_api_call(DBFS_GET_STATUS_ENDPOINT, {"path": dbfs_path})

    def read(self, dbfs_path: str, offset: int = 0, length: int = 524288) -> dict[str, Any]:
        """Read a chunk from a DBFS file."""
        return self._do_api_call(
            DBFS_READ_ENDPOINT,
            {
                "path": dbfs_path,
                "offset": offset,
                "length": length,
            },
        )

    def delete(self, dbfs_path: str, recursive: bool = False) -> None:
        """Delete a file or directory from DBFS."""
        self._do_api_call(DBFS_DELETE_ENDPOINT, {"path": dbfs_path, "recursive": recursive})

    def upload_file(self, local_path: str, dbfs_path: str, overwrite: bool = False) -> str:
        """Upload a local file to DBFS using multipart form data."""
        file_path = Path(local_path)
        if not file_path.is_file():
            raise AirflowException(f"Local file does not exist: {local_path}")

        _, endpoint = DBFS_PUT_ENDPOINT
        url = self._endpoint_url(f"api/{endpoint}")
        aad_headers = self._get_aad_headers()
        headers = {**self.user_agent_header, **aad_headers}

        token = self._get_token()
        if token:
            auth = _TokenAuth(token)
        else:
            self.log.info("Using basic auth.")
            auth = HTTPBasicAuth(self._get_connection_attr("login"), self.databricks_conn.password)

        try:
            for attempt in self._get_retry_object():
                with attempt:
                    with file_path.open("rb") as handle:
                        response = requests.post(
                            url,
                            data={"path": dbfs_path, "overwrite": str(overwrite).lower()},
                            files={"contents": (file_path.name, handle)},
                            auth=auth,
                            headers=headers,
                            timeout=self.timeout_seconds,
                        )
                        self.log.debug("Response Status Code: %s", response.status_code)
                        self.log.debug("Response text: %s", response.text)
                        response.raise_for_status()
                        return dbfs_path
        except RetryError:
            raise AirflowException(f"API requests to Databricks failed {self.retry_limit} times. Giving up.")
        except requests_exceptions.HTTPError as e:
            msg = f"Response: {e.response.content.decode()}, Status Code: {e.response.status_code}"
            raise AirflowException(msg)
        raise AirflowException("API request to Databricks returned without a response.")

    def download_file(
        self,
        dbfs_path: str,
        local_path: str,
        overwrite: bool = False,
        chunk_size: int = 524288,
    ) -> str:
        """Download a DBFS file to the local filesystem."""
        destination = Path(local_path)
        if destination.exists() and not overwrite:
            raise AirflowException(f"Local file already exists: {local_path}")

        status = self.get_status(dbfs_path)
        if status.get("is_dir"):
            raise AirflowException(f"DBFS path points to a directory: {dbfs_path}")

        destination.parent.mkdir(parents=True, exist_ok=True)
        offset = 0
        file_size = int(status.get("file_size", 0))
        temp_path: Path | None = None

        try:
            with NamedTemporaryFile(dir=destination.parent, delete=False) as temp_file:
                temp_path = Path(temp_file.name)
                with temp_path.open("wb") as handle:
                    while offset < file_size:
                        chunk = self.read(
                            dbfs_path, offset=offset, length=min(chunk_size, file_size - offset)
                        )
                        bytes_read = int(chunk["bytes_read"])
                        if bytes_read <= 0:
                            raise AirflowException(
                                f"Databricks returned an empty read before reaching EOF for {dbfs_path}"
                            )
                        handle.write(b64decode(chunk["data"]))
                        offset += bytes_read
            temp_path.replace(destination)
        except Exception:
            if temp_path is not None:
                temp_path.unlink(missing_ok=True)
            raise

        return local_path
