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
from typing import TYPE_CHECKING

from airflow.providers.common.compat.sdk import BaseHook

if TYPE_CHECKING:
    from airflow.providers.common.compat.sdk import Connection


log = logging.getLogger(__name__)


def _unwrap_method(method):
    return getattr(method, "__func__", method)


async def get_async_connection(conn_id: str, hook: BaseHook | type[BaseHook] | None = None) -> Connection:
    """
    Get an asynchronous Airflow connection that is backwards compatible.

    :param conn_id: The provided connection ID.
    :param hook: Hook instance or class used to resolve the connection.
    :returns: Connection
    """
    from asgiref.sync import sync_to_async

    hook = hook or BaseHook
    hook_cls = hook if isinstance(hook, type) else type(hook)
    base_hook_cls = BaseHook if isinstance(BaseHook, type) else type(BaseHook)
    hook_async = _unwrap_method(getattr(hook_cls, "aget_connection", None))
    base_hook_async = _unwrap_method(getattr(base_hook_cls, "aget_connection", None))

    if hook_async and (
        hook_cls is base_hook_cls or base_hook_async is None or hook_async is not base_hook_async
    ):
        log.debug("Get connection using `hook.aget_connection().")
        return await hook.aget_connection(conn_id=conn_id)
    log.debug("Get connection using `hook.get_connection().")
    return await sync_to_async(hook.get_connection)(conn_id=conn_id)


__all__ = [
    "get_async_connection",
]
