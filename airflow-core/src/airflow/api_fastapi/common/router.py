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

import inspect
from collections.abc import Callable
from typing import Any

from fastapi import APIRouter
from fastapi.params import Depends as DependsParam
from fastapi.types import DecoratedCallable

OPENAPI_AUTH_REQUIREMENTS_ATTR = "__airflow_openapi_auth_requirements__"


def _get_openapi_auth_requirements(dependencies: list[DependsParam] | None) -> tuple[str, ...]:
    if not dependencies:
        return ()
    requirements: list[str] = []
    for dependency in dependencies:
        callback = getattr(dependency, "dependency", None)
        dependency_requirements = getattr(callback, OPENAPI_AUTH_REQUIREMENTS_ATTR, ())
        requirements.extend(dependency_requirements)
    return tuple(dict.fromkeys(requirements))


def _append_openapi_auth_requirements(description: str | None, requirements: tuple[str, ...]) -> str | None:
    if not requirements:
        return description
    auth_note = "Authorization requirements:\n" + "\n".join(
        f"- {requirement}" for requirement in requirements
    )
    if not description:
        return auth_note
    return f"{description}\n\n{auth_note}"


def _get_route_description(endpoint: Callable[..., Any], explicit_description: str | None) -> str | None:
    if explicit_description is not None:
        return explicit_description
    return inspect.getdoc(endpoint)


class AirflowRouter(APIRouter):
    """Extends the FastAPI default router."""

    def add_api_route(self, path: str, endpoint: Callable[..., Any], **kwargs: Any) -> None:
        requirements = _get_openapi_auth_requirements(kwargs.get("dependencies"))
        if requirements:
            description = _get_route_description(endpoint, kwargs.get("description"))
            kwargs["description"] = _append_openapi_auth_requirements(description, requirements)
            openapi_extra = dict(kwargs.get("openapi_extra") or {})
            openapi_extra["x-airflow-authorization-requirements"] = list(requirements)
            kwargs["openapi_extra"] = openapi_extra
        super().add_api_route(path, endpoint, **kwargs)

    def api_route(
        self,
        path: str,
        operation_id: str | None = None,
        **kwargs: Any,
    ) -> Callable[[DecoratedCallable], DecoratedCallable]:
        def decorator(func: DecoratedCallable) -> DecoratedCallable:
            self.add_api_route(
                path,
                func,
                operation_id=operation_id or func.__name__,
                **kwargs,
            )
            return func

        return decorator
