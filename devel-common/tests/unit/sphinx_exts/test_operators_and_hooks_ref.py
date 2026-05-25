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

from sphinx_exts import operators_and_hooks_ref


def test_render_triggers(monkeypatch):
    monkeypatch.setattr(
        operators_and_hooks_ref,
        "load_package_data",
        lambda: [
            {
                "package-name": "apache-airflow-providers-http",
                "name": "HTTP",
                "triggers": [
                    {
                        "integration-name": "HTTP",
                        "python-modules": [
                            "airflow.providers.http.triggers.http",
                            "airflow.providers.http.triggers.another_http",
                        ],
                    }
                ],
            },
            {
                "package-name": "apache-airflow-providers-dummy",
                "name": "Dummy",
            },
        ],
    )

    rendered = operators_and_hooks_ref._common_render_list_content(
        header_separator="-",
        resource_type="triggers",
        template="triggers.rst.jinja2",
    )

    assert "HTTP" in rendered
    assert "- `HTTP`" in rendered
    assert ":mod:`airflow.providers.http.triggers.http`" in rendered
    assert ":mod:`airflow.providers.http.triggers.another_http`" in rendered
    assert "Dummy" not in rendered
