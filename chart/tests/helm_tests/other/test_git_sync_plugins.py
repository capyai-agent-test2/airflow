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

import jmespath
from chart_utils.helm_template_generator import render_chart


class TestGitSyncPlugins:
    """Test plugin git sync support."""

    def test_should_add_git_sync_container_to_api_server_if_persistence_is_disabled(self):
        docs = render_chart(
            values={"plugins": {"gitSync": {"enabled": True}, "persistence": {"enabled": False}}},
            show_only=["templates/api-server/api-server-deployment.yaml"],
        )

        assert jmespath.search("spec.template.spec.containers[1].name", docs[0]) == "git-sync"

    def test_should_add_plugins_volume_to_scheduler_if_git_sync_and_persistence_are_enabled(self):
        docs = render_chart(
            values={
                "executor": "LocalExecutor",
                "plugins": {"gitSync": {"enabled": True}, "persistence": {"enabled": True}},
            },
            show_only=["templates/scheduler/scheduler-deployment.yaml"],
        )

        assert "plugins" in jmespath.search("spec.template.spec.volumes[].name", docs[0])
        assert (
            len(
                jmespath.search(
                    "(spec.template.spec.containers[?name=='git-sync'].volumeMounts[])[?name=='plugins']",
                    docs[0],
                )
            )
            > 0
        )
