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

import sys
import types
from argparse import Namespace

import pytest

from airflow import __main__ as airflow_main
from airflow.cli.utils import get_structured_output_stream


@pytest.mark.parametrize(
    ("argv", "expected"),
    [
        (["dags", "list", "-o", "json"], True),
        (["dags", "list", "--output", "yaml"], True),
        (["dags", "list", "--output=json"], True),
        (["dags", "list", "-ojson"], True),
        (["dags", "list", "-o", "table"], False),
    ],
)
def test_has_machine_readable_output(argv, expected):
    assert airflow_main._has_machine_readable_output(argv) is expected


def test_main_redirects_pre_command_stdout_for_machine_readable_output(monkeypatch, capsys):
    parser = types.SimpleNamespace()
    args = Namespace(
        subcommand="dags",
        func=lambda _: print('[{"dag_id": "example"}]', file=get_structured_output_stream()),
    )
    parser.parse_args = lambda: args

    monkeypatch.setattr(
        airflow_main.configuration, "conf", types.SimpleNamespace(get=lambda *_, **__: "none")
    )
    monkeypatch.setattr(airflow_main.argcomplete, "autocomplete", lambda _: None)
    monkeypatch.setattr(
        "airflow.configuration.write_default_airflow_configuration_if_needed",
        lambda: airflow_main.configuration.conf,
    )
    monkeypatch.setattr(sys, "argv", ["airflow", "dags", "list", "-o", "json"])

    real_import = __import__

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "airflow.cli":
            print("pre-command log line")
            return types.SimpleNamespace(cli_parser=types.SimpleNamespace(get_parser=lambda: parser))
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr("builtins.__import__", fake_import)

    airflow_main.main()

    captured = capsys.readouterr()
    assert captured.out == '[{"dag_id": "example"}]\n'
    assert "pre-command log line" in captured.err
