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

import pytest
from fastapi import HTTPException
from wtforms import StringField, ValidationError

from airflow.api_fastapi.core_api.datamodels.connections import ConnectionBody
from airflow.api_fastapi.core_api.services.public import connections as public_connection_service
from airflow.models.connection import Connection
from airflow.providers_manager import ConnectionFormWidgetInfo


class TestValidateConnectionExtraFields:
    @pytest.fixture(autouse=True)
    def setup_connection_form_widgets(self, monkeypatch):
        self.calls = []

        def validate_authentication(form, field):
            self.calls.append(field.data)
            if field.data != "secEnterprise":
                raise ValidationError("Authentication method must be valid")

        cms_form_widget = ConnectionFormWidgetInfo(
            hook_class_name="CustomHook",
            package_name="custom-package",
            field=StringField(validators=[validate_authentication]),
            field_name="cms_authentication",
            is_sensitive=False,
        )
        other_form_widget = ConnectionFormWidgetInfo(
            hook_class_name="OtherHook",
            package_name="custom-package",
            field=StringField(validators=[validate_authentication]),
            field_name="cms_authentication",
            is_sensitive=False,
        )

        class MockProvidersManager:
            connection_form_widgets = {
                "extra__cms__cms_authentication": cms_form_widget,
                "extra__other__cms_authentication": other_form_widget,
            }

        monkeypatch.setattr(public_connection_service, "ProvidersManager", MockProvidersManager)

    @pytest.mark.parametrize(
        ("value", "expected_error"),
        [
            ("secEnterprise", None),
            ("invalid", "Authentication method must be valid"),
        ],
    )
    def test_legacy_custom_validator_is_called(self, value, expected_error):
        extra = json.dumps({"cms_authentication": value})
        if expected_error:
            with pytest.raises(HTTPException) as ctx:
                public_connection_service.validate_connection_extra_fields("cms", extra)

            assert ctx.value.status_code == 400
            assert ctx.value.detail == {"extra": {"cms_authentication": [expected_error]}}
        else:
            public_connection_service.validate_connection_extra_fields("cms", extra)

        assert self.calls == [value]

    def test_update_validation_uses_effective_persisted_extra(self):
        persisted_connection = Connection(
            conn_id="test_connection",
            conn_type="cms",
            extra=json.dumps({"cms_authentication": "secEnterprise"}),
        )
        update = ConnectionBody(
            connection_id="test_connection",
            conn_type="cms",
            extra=json.dumps({"unrelated": "value"}),
        )

        public_connection_service.validate_connection_update_extra_fields(
            persisted_connection,
            update,
            update_mask=["conn_type"],
        )

        assert self.calls == ["secEnterprise"]

    def test_update_validation_uses_persisted_conn_type_when_masked(self):
        persisted_connection = Connection(
            conn_id="test_connection",
            conn_type="cms",
            extra=json.dumps({"cms_authentication": "secEnterprise"}),
        )
        update = ConnectionBody(
            connection_id="test_connection",
            conn_type="other",
            extra=json.dumps({"cms_authentication": "invalid"}),
        )

        with pytest.raises(HTTPException) as ctx:
            public_connection_service.validate_connection_update_extra_fields(
                persisted_connection,
                update,
                update_mask=["extra"],
            )

        assert ctx.value.detail == {"extra": {"cms_authentication": ["Authentication method must be valid"]}}
        assert self.calls == ["invalid"]
