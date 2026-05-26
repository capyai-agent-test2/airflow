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

from types import SimpleNamespace

import pytest

from docs.utils.conf_constants import disable_suggest_change_button_for_autoapi_pages


@pytest.mark.parametrize(
    ("autoapi_root", "pagename"),
    [
        ("_api", "_api"),
        ("_api", "_api/airflow/providers/amazon/hooks/s3/index"),
        ("api", "api/airflow/sdk/index"),
    ],
)
def test_disable_suggest_change_button_for_autoapi_pages(autoapi_root, pagename):
    context = {
        "display_github": True,
        "meta": {"github_url": "https://example.invalid/edit-page", "other": "value"},
    }

    disable_suggest_change_button_for_autoapi_pages(
        SimpleNamespace(config=SimpleNamespace(autoapi_root=autoapi_root)),
        pagename,
        "page.html",
        context,
        None,
    )

    assert context["display_github"] is False
    assert context["meta"] == {"other": "value"}


def test_leave_suggest_change_button_enabled_for_non_autoapi_pages():
    context = {
        "display_github": True,
        "meta": {"github_url": "https://example.invalid/edit-page", "other": "value"},
    }

    disable_suggest_change_button_for_autoapi_pages(
        SimpleNamespace(config=SimpleNamespace(autoapi_root="_api")),
        "installation/index",
        "page.html",
        context,
        None,
    )

    assert context["display_github"] is True
    assert context["meta"] == {"github_url": "https://example.invalid/edit-page", "other": "value"}
