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
from argparse import ArgumentParser, Namespace

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


class _MachineReadableOutputParser(ArgumentParser):
    """ArgumentParser variant that does not exit on parse errors."""

    def error(self, message):
        raise ValueError(message)


def _build_machine_readable_output_parser() -> ArgumentParser:
    from airflow.cli import cli_config

    def add_command(subparsers, command) -> None:
        if isinstance(command, cli_config.ActionCommand):
            parser = subparsers.add_parser(command.name, add_help=False)
            for arg in command.args:
                arg.add_to_parser(parser)
            parser.set_defaults(_has_output_arg=cli_config.ARG_OUTPUT in command.args)
            return

        parser = subparsers.add_parser(command.name, add_help=False)
        nested_subparsers = parser.add_subparsers(dest=f"{command.name}_subcommand")
        for subcommand in command.subcommands:
            add_command(nested_subparsers, subcommand)

    parser = _MachineReadableOutputParser(add_help=False)
    subparsers = parser.add_subparsers(dest="subcommand")
    for command in cli_config.core_commands:
        add_command(subparsers, command)
    return parser


def _has_machine_readable_output(argv: list[str]) -> bool:
    """Check whether CLI args request machine-readable output."""
    if "--output" in argv or any(arg.startswith("--output=") for arg in argv):
        for index, arg in enumerate(argv):
            if arg == "--output":
                return index + 1 < len(argv) and argv[index + 1] in MACHINE_READABLE_OUTPUTS
            if arg.startswith("--output="):
                return arg.partition("=")[2] in MACHINE_READABLE_OUTPUTS

    try:
        parsed_args, _ = _build_machine_readable_output_parser().parse_known_args(argv, namespace=Namespace())
    except ValueError:
        return False

    return (
        getattr(parsed_args, "_has_output_arg", False)
        and getattr(parsed_args, "output", None) in MACHINE_READABLE_OUTPUTS
    )


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
