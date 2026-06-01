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

import jmespath
import pytest
from chart_utils.helm_template_generator import HelmFailedError, render_chart
from cryptography.fernet import Fernet


class TestFernetKeySecret:
    """Tests fernet key secret."""

    def test_should_add_annotations_to_fernetkey_secret(self):
        # Create a Fernet key
        fernet_key_provided = Fernet.generate_key().decode()
        docs = render_chart(
            values={
                "fernetKey": fernet_key_provided,
                "fernetKeySecretAnnotations": {"test_annotation": "test_annotation_value"},
            },
            show_only=["templates/secrets/fernetkey-secret.yaml"],
        )[0]
        assert "annotations" in jmespath.search("metadata", docs)
        assert jmespath.search("metadata.annotations", docs)["test_annotation"] == "test_annotation_value"

        # Extract the base64 encoded fernet key from the secret
        fernet_key_b64 = jmespath.search('data."fernet-key"', docs).strip('"')
        fernet_key = base64.b64decode(fernet_key_b64).decode()

        # Verify the key is valid by creating a Fernet instance
        Fernet(fernet_key.encode())  # Raise: Fernet key must be 32 url-safe base64-encoded bytes.

    def test_should_generate_valid_fernetkey_secret(self):
        """Test that a valid Fernet key is generated."""
        # No fernetKey provided
        docs = render_chart(show_only=["templates/secrets/fernetkey-secret.yaml"])[0]

        # Extract the base64 encoded fernet key from the secret
        fernet_key_b64 = jmespath.search('data."fernet-key"', docs).strip('"')
        fernet_key = base64.b64decode(fernet_key_b64).decode()

        # Verify the key is valid by creating a Fernet instance
        Fernet(fernet_key.encode())  # Raise: Fernet key must be 32 url-safe base64-encoded bytes.

    def test_should_disable_helm_hooks_for_fernetkey_secret(self):
        fernet_key_provided = Fernet.generate_key().decode()
        docs = render_chart(
            values={
                "fernetKey": fernet_key_provided,
                "fernetKeySecretAnnotations": {"test_annotation": "test_annotation_value"},
                "fernetKeySecretUseHelmHooks": False,
            },
            show_only=["templates/secrets/fernetkey-secret.yaml"],
        )[0]

        annotations = docs["metadata"]["annotations"]
        assert annotations == {"test_annotation": "test_annotation_value"}

    def test_should_require_stable_fernet_key_when_disabling_helm_hooks(self):
        with pytest.raises(HelmFailedError) as ex_ctx:
            render_chart(
                values={"fernetKeySecretUseHelmHooks": False},
                show_only=["templates/secrets/fernetkey-secret.yaml"],
            )

        assert (
            "When disabling fernetKeySecretUseHelmHooks, you must set either fernetKey or "
            "fernetKeySecretName to keep the Fernet key stable across syncs." in ex_ctx.value.stderr.decode()
        )
