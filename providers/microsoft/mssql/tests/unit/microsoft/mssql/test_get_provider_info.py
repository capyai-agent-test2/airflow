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

from airflow.providers.microsoft.mssql.get_provider_info import get_provider_info


def test_mssql_connection_schema_field_is_labeled_as_database():
    provider_info = get_provider_info()

    mssql_connection = next(
        connection_type
        for connection_type in provider_info["connection-types"]
        if connection_type["connection-type"] == "mssql"
    )
    assert mssql_connection["ui-field-behaviour"] == {"relabeling": {"schema": "Database"}}
