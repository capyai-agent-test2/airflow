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

import pytest

from airflow.providers.common.compat.sdk import AirflowException
from airflow.providers.http.exceptions import HttpErrorException, HttpMethodException


@pytest.mark.parametrize(
    ("exception_cls", "message"),
    [
        (HttpErrorException, "Request failed"),
        (HttpMethodException, "Method must be GET"),
    ],
)
def test_http_exceptions_are_airflow_exceptions(exception_cls, message):
    with pytest.raises(AirflowException, match=message):
        raise exception_cls(message)
