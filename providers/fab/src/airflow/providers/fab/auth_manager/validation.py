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

import re

from wtforms import ValidationError

HTML_UNSAFE_CHARACTER_MESSAGE = "must not contain `<` or `>` characters"

_HTML_UNSAFE_CHARACTER_PATTERN = re.compile(r"[<>]")


def validate_html_safe_text(value: str) -> str:
    """Reject text that can be interpreted as HTML tags."""
    if _HTML_UNSAFE_CHARACTER_PATTERN.search(value):
        raise ValueError(HTML_UNSAFE_CHARACTER_MESSAGE)
    return value


def validate_html_safe_form_field(_form, field) -> None:
    """Reject form values that can be interpreted as HTML tags."""
    if field.data is not None:
        try:
            validate_html_safe_text(field.data)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
