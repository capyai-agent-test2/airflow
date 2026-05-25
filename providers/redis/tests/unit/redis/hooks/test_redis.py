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

from unittest import mock

import pytest

from airflow.models import Connection
from airflow.providers.redis.hooks.redis import RedisHook


class TestRedisHook:
    @pytest.mark.db_test
    def test_get_conn(self):
        hook = RedisHook(redis_conn_id="redis_default")
        assert hook.redis is None

        assert hook.host is None, "host initialised as None."
        assert hook.port is None, "port initialised as None."
        assert hook.password is None, "password initialised as None."
        assert hook.db is None, "db initialised as None."
        assert hook.get_conn() is hook.get_conn(), "Connection initialized only if None."

    @mock.patch("airflow.providers.redis.hooks.redis.Redis")
    @mock.patch(
        "airflow.providers.redis.hooks.redis.RedisHook.get_connection",
    )
    def test_get_conn_with_extra_config(self, mock_get_connection, mock_redis):
        connection = Connection(
            login="user",
            password="password",
            host="remote_host",
            port=1234,
        )
        connection.set_extra(
            """{
                "db": 2,
                "ssl": true,
                "ssl_cert_reqs": "required",
                "ssl_ca_certs": "/path/to/custom/ca-cert",
                "ssl_keyfile": "/path/to/key-file",
                "ssl_certfile": "/path/to/cert-file",
                "ssl_check_hostname": true
            }"""
        )
        mock_get_connection.return_value = connection
        hook = RedisHook()

        hook.get_conn()
        mock_redis.assert_called_once_with(
            host=connection.host,
            username=connection.login,
            password=connection.password,
            port=connection.port,
            db=connection.extra_dejson["db"],
            ssl=connection.extra_dejson["ssl"],
            ssl_cert_reqs=connection.extra_dejson["ssl_cert_reqs"],
            ssl_ca_certs=connection.extra_dejson["ssl_ca_certs"],
            ssl_keyfile=connection.extra_dejson["ssl_keyfile"],
            ssl_certfile=connection.extra_dejson["ssl_certfile"],
            ssl_check_hostname=connection.extra_dejson["ssl_check_hostname"],
        )

    @mock.patch("airflow.providers.redis.hooks.redis.RedisCluster")
    @mock.patch(
        "airflow.providers.redis.hooks.redis.RedisHook.get_connection",
    )
    def test_get_conn_with_cluster_mode(self, mock_get_connection, mock_redis_cluster):
        connection = Connection(
            login="user",
            password="password",
            host="remote_host",
            port=1234,
        )
        connection.set_extra(
            """{
                "cluster": true,
                "ssl": true
            }"""
        )
        mock_get_connection.return_value = connection
        hook = RedisHook()

        hook.get_conn()
        mock_redis_cluster.assert_called_once_with(
            host=connection.host,
            port=connection.port,
            username=connection.login,
            password=connection.password,
            ssl=connection.extra_dejson["ssl"],
        )

    @mock.patch("airflow.providers.redis.hooks.redis.RedisCluster")
    @mock.patch(
        "airflow.providers.redis.hooks.redis.RedisHook.get_connection",
    )
    def test_get_conn_with_cluster_startup_nodes(self, mock_get_connection, mock_redis_cluster):
        connection = Connection(
            login="user",
            password="password",
        )
        connection.set_extra(
            """{
                "cluster": true,
                "startup_nodes": [
                    {"host": "redis-1", "port": 6379},
                    {"host": "redis-2", "port": 6380}
                ]
            }"""
        )
        mock_get_connection.return_value = connection
        hook = RedisHook()

        hook.get_conn()
        startup_nodes = mock_redis_cluster.call_args.kwargs["startup_nodes"]
        assert [(node.host, node.port) for node in startup_nodes] == [("redis-1", 6379), ("redis-2", 6380)]
        assert mock_redis_cluster.call_args.kwargs["username"] == connection.login
        assert mock_redis_cluster.call_args.kwargs["password"] == connection.password

    @pytest.mark.db_test
    def test_get_conn_password_stays_none(self):
        hook = RedisHook(redis_conn_id="redis_default")
        hook.get_conn()
        assert hook.password is None
