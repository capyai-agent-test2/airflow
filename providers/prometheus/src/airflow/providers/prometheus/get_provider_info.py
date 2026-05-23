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


def get_provider_info():
    return {
        "package-name": "apache-airflow-providers-prometheus",
        "name": "Prometheus",
        "description": "`Prometheus <https://prometheus.io/>`__ provider with Pushgateway support for Airflow tasks.\n",
        "integrations": [
            {
                "integration-name": "Prometheus",
                "external-doc-url": "https://prometheus.io/docs/instrumenting/pushing/",
                "tags": ["software"],
            }
        ],
        "hooks": [
            {
                "integration-name": "Prometheus",
                "python-modules": ["airflow.providers.prometheus.hooks.prometheus"],
            }
        ],
        "connection-types": [
            {
                "hook-class-name": "airflow.providers.prometheus.hooks.prometheus.PrometheusHook",
                "hook-name": "Prometheus",
                "connection-type": "prometheus",
            }
        ],
    }
