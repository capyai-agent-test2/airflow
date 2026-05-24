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

from flask import Flask
from flask_babel import lazy_gettext

from airflow.providers.fab.www.session import (
    AirflowSecureCookieSessionInterface,
    _LazySafeMsgpackSerializer,
)


def test_lazy_safe_msgpack_serializer_preserves_database_session_payloads():
    serializer = _LazySafeMsgpackSerializer()

    payload = serializer.dumps({"flash": [lazy_gettext("Login")], "local": lazy_gettext("en")})

    assert isinstance(payload, bytes)
    assert serializer.loads(payload) == {"flash": ["Login"], "local": "en"}


def test_secure_cookie_session_serializer_returns_cookie_safe_string():
    app = Flask(__name__)
    app.secret_key = "secret"
    serializer = AirflowSecureCookieSessionInterface().get_signing_serializer(app)

    payload = serializer.dumps({"flash": [lazy_gettext("Login")], "local": lazy_gettext("en")})

    assert isinstance(payload, str)
    assert serializer.loads(payload) == {"flash": ["Login"], "local": "en"}
