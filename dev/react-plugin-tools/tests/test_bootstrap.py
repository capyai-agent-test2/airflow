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

# ruff: noqa: S101

from __future__ import annotations

import importlib.util
from argparse import Namespace
from pathlib import Path

import pytest


def _load_bootstrap_module():
    module_path = Path(__file__).resolve().parents[1] / "bootstrap.py"
    spec = importlib.util.spec_from_file_location("react_plugin_bootstrap", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


bootstrap = _load_bootstrap_module()


def test_should_include_ai_rules_honors_explicit_true():
    args = Namespace(include_ai_rules=True)

    assert bootstrap.should_include_ai_rules(args) is True


def test_should_include_ai_rules_honors_explicit_false():
    args = Namespace(include_ai_rules=False)

    assert bootstrap.should_include_ai_rules(args) is False


def test_should_include_ai_rules_defaults_to_false_without_tty(monkeypatch, capsys):
    args = Namespace(include_ai_rules=None)
    monkeypatch.setattr(bootstrap.sys.stdin, "isatty", lambda: False)

    assert bootstrap.should_include_ai_rules(args) is False
    assert "skipping AI agent coding rules" in capsys.readouterr().out


@pytest.mark.parametrize("include_ai_rules", [True, False])
def test_copy_template_files_respects_ai_rules_selection(tmp_path, include_ai_rules):
    project_path = tmp_path / "plugin"

    bootstrap.copy_template_files(
        template_dir=bootstrap.get_template_dir(),
        project_path=project_path,
        project_name="demo-plugin",
        include_ai_rules=include_ai_rules,
    )

    ai_rules_dir = project_path / "ai-agent-rules"
    readme_path = project_path / "README.md"

    assert readme_path.exists()
    assert "demo-plugin" in readme_path.read_text(encoding="utf-8")
    assert ai_rules_dir.exists() is include_ai_rules
