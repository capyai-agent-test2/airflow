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

import typing
from contextlib import contextmanager
from typing import Any, cast

from jupyter_client import AsyncKernelManager
from papermill.clientwrap import PapermillNotebookClient
from papermill.engines import NBClientEngine
from papermill.utils import merge_kwargs, remove_args
from traitlets import Unicode

from airflow.providers.common.compat.sdk import BaseHook

JUPYTER_KERNEL_SHELL_PORT = 60316
JUPYTER_KERNEL_IOPUB_PORT = 60317
JUPYTER_KERNEL_STDIN_PORT = 60318
JUPYTER_KERNEL_CONTROL_PORT = 60319
JUPYTER_KERNEL_HB_PORT = 60320
REMOTE_KERNEL_ENGINE = "remote_kernel_engine"
GATEWAY_KERNEL_ENGINE = "gateway_kernel_engine"


class KernelConnection:
    """Class to represent kernel connection object."""

    ip: str
    gateway_url: str | None
    gateway_ws_url: str | None
    shell_port: int
    iopub_port: int
    stdin_port: int
    control_port: int
    hb_port: int
    session_key: str
    auth_token: str | None
    auth_scheme: str | None
    validate_cert: bool


class KernelHook(BaseHook):
    """
    The KernelHook can be used to interact with remote jupyter kernel.

    Takes kernel host/ip from connection and refers to jupyter kernel ports and session_key
     from ``extra`` field.

    :param kernel_conn_id: connection that has kernel host/ip
    """

    conn_name_attr = "kernel_conn_id"
    default_conn_name = "jupyter_kernel_default"
    conn_type = "jupyter_kernel"
    hook_name = "Jupyter Kernel"

    def __init__(self, kernel_conn_id: str = default_conn_name, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.kernel_conn = self.get_connection(kernel_conn_id)
        register_remote_kernel_engine()

    def get_conn(self) -> KernelConnection:
        kernel_connection = KernelConnection()
        extra = self.kernel_conn.extra_dejson
        host = cast("str", self.kernel_conn.host)
        gateway_url = extra.get("gateway_url")
        if gateway_url is None and host.startswith(("http://", "https://")):
            gateway_url = host

        kernel_connection.ip = host
        kernel_connection.gateway_url = gateway_url
        kernel_connection.gateway_ws_url = extra.get("gateway_ws_url")
        kernel_connection.shell_port = extra.get("shell_port", JUPYTER_KERNEL_SHELL_PORT)
        kernel_connection.iopub_port = extra.get("iopub_port", JUPYTER_KERNEL_IOPUB_PORT)
        kernel_connection.stdin_port = extra.get("stdin_port", JUPYTER_KERNEL_STDIN_PORT)
        kernel_connection.control_port = extra.get("control_port", JUPYTER_KERNEL_CONTROL_PORT)
        kernel_connection.hb_port = extra.get("hb_port", JUPYTER_KERNEL_HB_PORT)
        kernel_connection.session_key = extra.get("session_key", "")
        password = cast("str | None", self.kernel_conn.password)
        kernel_connection.auth_token = (
            password if isinstance(password, str) and password else extra.get("auth_token")
        )
        kernel_connection.auth_scheme = extra.get("auth_scheme")
        kernel_connection.validate_cert = extra.get("validate_cert", True)
        return kernel_connection


def register_remote_kernel_engine():
    """Register remote papermill engines."""
    from papermill.engines import papermill_engines

    papermill_engines.register(REMOTE_KERNEL_ENGINE, RemoteKernelEngine)
    papermill_engines.register(GATEWAY_KERNEL_ENGINE, GatewayKernelEngine)


class RemoteKernelManager(AsyncKernelManager):
    """Jupyter kernel manager that connects to a remote kernel."""

    session_key = Unicode("", config=True, help="Session key to connect to remote kernel")

    @property
    def has_kernel(self) -> bool:
        return True

    async def _async_is_alive(self) -> bool:
        return True

    def shutdown_kernel(self, now: bool = False, restart: bool = False):
        pass

    def client(self, **kwargs: typing.Any):
        """Create a client configured to connect to our kernel."""
        kernel_client = super().client(**kwargs)
        # load connection info to set session_key
        config: dict[str, int | str | bytes] = dict(
            ip=self.ip,
            shell_port=self.shell_port,
            iopub_port=self.iopub_port,
            stdin_port=self.stdin_port,
            control_port=self.control_port,
            hb_port=self.hb_port,
            key=self.session_key,
            transport="tcp",
            signature_scheme="hmac-sha256",
        )
        kernel_client.load_connection_info(config)
        return kernel_client


class RemoteKernelEngine(NBClientEngine):
    """Papermill engine to use ``RemoteKernelManager`` to connect to remote kernel and execute notebook."""

    @classmethod
    def execute_managed_notebook(
        cls,
        nb_man,
        kernel_name,
        log_output=False,
        stdout_file=None,
        stderr_file=None,
        start_timeout=60,
        execution_timeout=None,
        **kwargs,
    ):
        """Perform the actual execution of the parameterized notebook locally."""
        km = RemoteKernelManager()
        km.ip = kwargs["kernel_ip"]
        km.shell_port = kwargs["kernel_shell_port"]
        km.iopub_port = kwargs["kernel_iopub_port"]
        km.stdin_port = kwargs["kernel_stdin_port"]
        km.control_port = kwargs["kernel_control_port"]
        km.hb_port = kwargs["kernel_hb_port"]
        km.ip = kwargs["kernel_ip"]
        km.session_key = kwargs["kernel_session_key"]

        # Exclude parameters that named differently downstream
        safe_kwargs = remove_args(["timeout", "startup_timeout"], **kwargs)

        final_kwargs = merge_kwargs(
            safe_kwargs,
            timeout=execution_timeout if execution_timeout else kwargs.get("timeout"),
            startup_timeout=start_timeout,
            log_output=False,
            stdout_file=stdout_file,
            stderr_file=stderr_file,
        )

        return PapermillNotebookClient(nb_man, km=km, **final_kwargs).execute()


@contextmanager
def configured_gateway_client(**kwargs: Any):
    """Temporarily configure the Jupyter gateway client for notebook execution."""
    from jupyter_server.gateway.gateway_client import GatewayClient

    gateway_client = GatewayClient.instance()
    original_values = {
        "url": gateway_client.url,
        "ws_url": gateway_client.ws_url,
        "auth_token": gateway_client.auth_token,
        "auth_scheme": gateway_client.auth_scheme,
        "validate_cert": gateway_client.validate_cert,
    }
    try:
        for key, value in kwargs.items():
            setattr(gateway_client, key, value)
        gateway_client._connection_args = {}
        yield
    finally:
        for key, value in original_values.items():
            setattr(gateway_client, key, value)
        gateway_client._connection_args = {}


class GatewayKernelEngine(NBClientEngine):
    """Papermill engine that starts kernels through a Jupyter Gateway over HTTP or HTTPS."""

    @classmethod
    def execute_managed_notebook(
        cls,
        nb_man,
        kernel_name,
        log_output=False,
        stdout_file=None,
        stderr_file=None,
        start_timeout=60,
        execution_timeout=None,
        **kwargs,
    ):
        """Perform the actual execution of the parameterized notebook through a gateway server."""
        gateway_url = kwargs["gateway_url"]
        gateway_ws_url = kwargs.get("gateway_ws_url") or gateway_url.replace("http", "ws", 1)
        safe_kwargs = remove_args(
            [
                "timeout",
                "startup_timeout",
                "gateway_url",
                "gateway_ws_url",
                "gateway_auth_token",
                "gateway_auth_scheme",
                "gateway_validate_cert",
            ],
            **kwargs,
        )

        final_kwargs = merge_kwargs(
            safe_kwargs,
            timeout=execution_timeout if execution_timeout else kwargs.get("timeout"),
            startup_timeout=start_timeout,
            kernel_name=kernel_name,
            kernel_manager_class="jupyter_server.gateway.managers.GatewayKernelManager",
            log_output=log_output,
            stdout_file=stdout_file,
            stderr_file=stderr_file,
        )

        with configured_gateway_client(
            url=gateway_url,
            ws_url=gateway_ws_url,
            auth_token=kwargs.get("gateway_auth_token", ""),
            auth_scheme=kwargs.get("gateway_auth_scheme", "token"),
            validate_cert=kwargs.get("gateway_validate_cert", True),
        ):
            return PapermillNotebookClient(nb_man, **final_kwargs).execute(kernel_name=kernel_name)
