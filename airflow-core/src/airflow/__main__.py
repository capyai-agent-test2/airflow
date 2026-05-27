#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK
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
"""Main executable module."""

from __future__ import annotations

import io
import os
import sys
from collections.abc import Iterable
from contextlib import contextmanager

import argcomplete

# The configuration module initializes and validates the conf object as a side effect the first
# time it is imported. If it is not imported before importing the settings module, the conf
# object will then be initted/validated as a side effect of it being imported in settings,
# however this can cause issues since those modules are very tightly coupled and can
# very easily cause import cycles in the conf init/validate code (since downstream code from
# those functions likely import settings).
# Therefore importing configuration early (as the first airflow import) avoids
# any possible import cycles with settings downstream.
from airflow import configuration

MACHINE_READABLE_OUTPUTS = {"json", "yaml"}


@contextmanager
def _redirect_stdout_to_stderr():
    original_stdout = sys.stdout
    saved_stdout_fd: int | None = None
    try:
        try:
            saved_stdout_fd = os.dup(original_stdout.fileno())
        except (AttributeError, OSError, io.UnsupportedOperation):
            sys.stdout = sys.stderr
            yield
            return

        os.dup2(sys.stderr.fileno(), original_stdout.fileno())
        sys.stdout = sys.stderr
        yield
    finally:
        if saved_stdout_fd is not None:
            os.dup2(saved_stdout_fd, original_stdout.fileno())
            os.close(saved_stdout_fd)
        sys.stdout = original_stdout


def _has_output_arg(command_args) -> bool:
    return any("-o" in arg.flags and "--output" in arg.flags for arg in command_args)


def _find_selected_action(commands: Iterable, argv: list[str]):
    from airflow.cli import cli_config

    selected_commands = list(commands)
    selected_action = None

    for arg in argv:
        command = next((command for command in selected_commands if command.name == arg), None)
        if command is None:
            continue
        if isinstance(command, cli_config.GroupCommand):
            selected_commands = list(command.subcommands)
            continue
        selected_action = command
        break

    return selected_action


def _find_machine_readable_output_value(argv: list[str]) -> str | None:
    selected_output = None
    index = 0
    while index < len(argv):
        arg = argv[index]
        if arg in {"-o", "--output"}:
            if index + 1 < len(argv):
                selected_output = argv[index + 1]
                index += 2
                continue
            break
        if arg.startswith("--output="):
            selected_output = arg.partition("=")[2]
        elif arg.startswith("-o") and len(arg) > 2:
            selected_output = arg[2:]
        index += 1
    return selected_output


def _has_machine_readable_output(argv: list[str]) -> bool:
    """Check whether CLI args request machine-readable output."""
    output_value = _find_machine_readable_output_value(argv)
    if output_value not in MACHINE_READABLE_OUTPUTS:
        return False

    from airflow.cli import cli_config

    if action := _find_selected_action(cli_config.core_commands, argv):
        return _has_output_arg(action.args)

    with _redirect_stdout_to_stderr():
        from airflow.cli import cli_parser

        if action := _find_selected_action(cli_parser.airflow_commands, argv):
            return _has_output_arg(action.args)
    return False


def main():
    conf = configuration.conf
    if conf.get("core", "security") == "kerberos":
        os.environ["KRB5CCNAME"] = conf.get("kerberos", "ccache")
        os.environ["KRB5_KTNAME"] = conf.get("kerberos", "keytab")
    original_stdout = sys.stdout
    should_redirect_stdout = _has_machine_readable_output(sys.argv[1:])
    saved_stdout_fd: int | None = None
    structured_output_stream = None
    from airflow.cli.utils import set_structured_output_stream

    if should_redirect_stdout:
        try:
            saved_stdout_fd = os.dup(original_stdout.fileno())
        except (AttributeError, OSError, io.UnsupportedOperation):
            structured_output_stream = original_stdout
        else:
            structured_output_stream = os.fdopen(os.dup(saved_stdout_fd), mode="w", buffering=1)
            os.dup2(sys.stderr.fileno(), original_stdout.fileno())

        set_structured_output_stream(structured_output_stream)
        sys.stdout = sys.stderr

    try:
        from airflow.cli import cli_parser

        parser = cli_parser.get_parser()
        argcomplete.autocomplete(parser)
        args = parser.parse_args()
        if args.subcommand not in ["lazy_loaded", "version"]:
            # Here we ensure that the default configuration is written if needed before running any command
            # that might need it. This used to be done during configuration initialization but having it
            # in main ensures that it is not done during tests and other ways airflow imports are used
            from airflow.configuration import write_default_airflow_configuration_if_needed

            conf = write_default_airflow_configuration_if_needed()

        if should_redirect_stdout:
            if saved_stdout_fd is not None:
                os.dup2(saved_stdout_fd, original_stdout.fileno())
                os.close(saved_stdout_fd)
                saved_stdout_fd = None
            sys.stdout = original_stdout

        args.func(args)
    finally:
        if should_redirect_stdout:
            if saved_stdout_fd is not None:
                os.dup2(saved_stdout_fd, original_stdout.fileno())
                os.close(saved_stdout_fd)
            sys.stdout = original_stdout
            if structured_output_stream is not None and structured_output_stream is not original_stdout:
                structured_output_stream.close()
            set_structured_output_stream(None)


if __name__ == "__main__":
    main()
