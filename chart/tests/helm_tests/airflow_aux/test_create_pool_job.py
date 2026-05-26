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

import jmespath
from chart_utils.helm_template_generator import render_chart


class TestCreatePoolJob:
    """Tests create pool job."""

    def test_should_not_render_by_default(self):
        docs = render_chart(show_only=["templates/jobs/create-pool-job.yaml"])
        assert docs == []

    def test_should_render_with_pools(self):
        docs = render_chart(
            values={
                "pools": [
                    {"name": "default_pool", "slots": 64, "description": "Default pool"},
                    {"name": "deferred_pool", "slots": 8, "includeDeferred": True},
                ]
            },
            show_only=[
                "templates/configmaps/pools-configmap.yaml",
                "templates/jobs/create-pool-job-serviceaccount.yaml",
                "templates/jobs/create-pool-job.yaml",
            ],
        )

        assert [doc["kind"] for doc in docs] == ["ConfigMap", "ServiceAccount", "Job"]
        assert jmespath.search("metadata.name", docs[1]) == "release-name-airflow-create-pool-job"
        assert jmespath.search("spec.template.spec.containers[0].name", docs[2]) == "create-pool"
        assert docs[2]["metadata"]["annotations"]["helm.sh/hook-weight"] == "3"
        assert (
            jmespath.search("spec.template.spec.volumes[1].configMap.name", docs[2]) == "release-name-pools"
        )

        pools_json = json.loads(docs[0]["data"]["pools.json"])
        assert pools_json == {
            "default_pool": {"slots": 64, "description": "Default pool", "include_deferred": False},
            "deferred_pool": {"slots": 8, "description": "", "include_deferred": True},
        }

    def test_should_disable_default_helm_hooks(self):
        docs = render_chart(
            values={
                "pools": [{"name": "default_pool", "slots": 64}],
                "createPoolJob": {"useHelmHooks": False},
            },
            show_only=["templates/jobs/create-pool-job.yaml"],
        )
        annotations = jmespath.search("metadata.annotations", docs[0])
        assert annotations is None
