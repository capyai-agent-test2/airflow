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

from configparser import ConfigParser

import pytest
from opentelemetry.sdk.resources import SERVICE_NAME
from opentelemetry.trace import NonRecordingSpan, SpanContext, TraceFlags, TraceState
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

from airflow_shared.observability.traces import (
    DEFAULT_TASK_SPAN_DETAIL_LEVEL,
    TASK_SPAN_DETAIL_LEVEL_KEY,
    _get_backcompat_config,
    build_trace_state_entries,
    get_task_span_detail_level,
    new_dagrun_trace_carrier,
)


@pytest.fixture
def traces_conf(monkeypatch):
    monkeypatch.delenv("OTEL_SERVICE_NAME", raising=False)
    conf = ConfigParser()
    conf.add_section("traces")
    conf.set("traces", "otel_service", "Airflow")
    return conf


class TestGetBackcompatConfig:
    def test_merges_deprecated_service_with_resource_attributes(self, monkeypatch, traces_conf):
        monkeypatch.setenv(
            "OTEL_RESOURCE_ATTRIBUTES", "deployment.environment.name=prd,service.version=v0.0.7"
        )

        _, resource = _get_backcompat_config(traces_conf)

        assert resource is not None
        assert resource.attributes[SERVICE_NAME] == "Airflow"
        assert resource.attributes["deployment.environment.name"] == "prd"
        assert resource.attributes["service.version"] == "v0.0.7"

    def test_resource_attribute_service_name_takes_precedence(self, monkeypatch, traces_conf):
        monkeypatch.setenv("OTEL_RESOURCE_ATTRIBUTES", "service.name=CustomService")

        _, resource = _get_backcompat_config(traces_conf)

        assert resource is not None
        assert resource.attributes[SERVICE_NAME] == "CustomService"

    def test_otel_service_name_env_takes_precedence(self, monkeypatch, traces_conf):
        monkeypatch.setenv("OTEL_SERVICE_NAME", "CustomService")

        _, resource = _get_backcompat_config(traces_conf)

        assert resource is None


class TestBuildTraceStateEntries:
    def test_with_integer_level(self):
        entries = build_trace_state_entries(2)
        assert entries == [(TASK_SPAN_DETAIL_LEVEL_KEY, "2")]

    def test_with_string_level(self):
        entries = build_trace_state_entries("3")
        assert entries == [(TASK_SPAN_DETAIL_LEVEL_KEY, "3")]

    def test_with_none(self):
        assert build_trace_state_entries(None) == []

    def test_with_zero(self):
        # 0 is falsy — treated as no detail level
        assert build_trace_state_entries(0) == []

    def test_with_invalid_string(self):
        # Non-integer string should not raise; returns empty
        assert build_trace_state_entries("not-a-number") == []


class TestNewDagrunTraceCarrier:
    def test_with_detail_level_embeds_level_in_trace_state(self):
        carrier = new_dagrun_trace_carrier(task_span_detail_level=2)
        ctx = TraceContextTextMapPropagator().extract(carrier)
        from opentelemetry import trace

        span_ctx = trace.get_current_span(ctx).get_span_context()
        assert span_ctx.trace_state.get(TASK_SPAN_DETAIL_LEVEL_KEY) == "2"

    def test_without_detail_level_has_empty_trace_state(self):
        carrier = new_dagrun_trace_carrier()
        ctx = TraceContextTextMapPropagator().extract(carrier)
        from opentelemetry import trace

        span_ctx = trace.get_current_span(ctx).get_span_context()
        assert span_ctx.trace_state.get(TASK_SPAN_DETAIL_LEVEL_KEY) is None


class TestGetTaskSpanDetailLevel:
    def _make_span_with_trace_state(self, entries: list[tuple[str, str]]) -> NonRecordingSpan:
        from opentelemetry.sdk.trace.id_generator import RandomIdGenerator

        gen = RandomIdGenerator()
        span_ctx = SpanContext(
            trace_id=gen.generate_trace_id(),
            span_id=gen.generate_span_id(),
            is_remote=False,
            trace_flags=TraceFlags(TraceFlags.SAMPLED),
            trace_state=TraceState(entries=entries),
        )
        return NonRecordingSpan(span_ctx)

    def test_returns_default_when_no_trace_state(self):
        span = self._make_span_with_trace_state([])
        assert get_task_span_detail_level(span) == DEFAULT_TASK_SPAN_DETAIL_LEVEL

    def test_reads_level_from_trace_state(self):
        span = self._make_span_with_trace_state([(TASK_SPAN_DETAIL_LEVEL_KEY, "2")])
        assert get_task_span_detail_level(span) == 2

    def test_fallback_on_invalid_value(self):
        span = self._make_span_with_trace_state([(TASK_SPAN_DETAIL_LEVEL_KEY, "bad")])
        assert get_task_span_detail_level(span) == DEFAULT_TASK_SPAN_DETAIL_LEVEL

    def test_roundtrip_via_carrier(self):
        """Level set in new_dagrun_trace_carrier is readable by get_task_span_detail_level."""
        carrier = new_dagrun_trace_carrier(task_span_detail_level=3)
        ctx = TraceContextTextMapPropagator().extract(carrier)
        from opentelemetry import trace

        span = trace.get_current_span(ctx)
        assert get_task_span_detail_level(span) == 3
