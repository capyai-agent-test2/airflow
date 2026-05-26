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

from abc import ABC, abstractmethod
from collections.abc import Iterable
from typing import TYPE_CHECKING, Any, Generic, TypeVar, Union, get_args, get_origin

from fastapi import HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel as PydanticBaseModel, ConfigDict, create_model

if TYPE_CHECKING:
    from sqlalchemy.sql import Select

T = TypeVar("T")


class BaseModel(PydanticBaseModel):
    """
    Base pydantic model for REST API.

    :meta private:
    """

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class StrictBaseModel(BaseModel):
    """
    StrictBaseModel is a base Pydantic model for REST API that does not allow any extra fields.

    Use this class for models that should not have any extra fields in the payload.

    :meta private:
    """

    model_config = ConfigDict(from_attributes=True, populate_by_name=True, extra="forbid")


def make_partial_model(model: type[PydanticBaseModel]) -> type[PydanticBaseModel]:
    """Create a version of a Pydantic model where all fields are Optional with default=None."""
    field_overrides: dict = {}
    for field_name, field_info in model.model_fields.items():
        ann = field_info.annotation
        origin = get_origin(ann)
        if not (origin is Union and type(None) in get_args(ann)):
            ann = ann | None  # type: ignore[operator, assignment]
        new_info = field_info._copy()
        new_info.default = None
        new_info._attributes_set["default"] = None
        field_overrides[field_name] = (ann, new_info)

    return create_model(
        f"{model.__name__}Partial",
        __base__=model,
        **field_overrides,
    )


def split_requested_fields(fields: list[str] | None) -> list[str] | None:
    """Normalize repeated or comma-separated field selectors."""
    if not fields:
        return None
    normalized_fields: list[str] = []
    for field_group in fields:
        for field in field_group.split(","):
            normalized_field = field.strip()
            if normalized_field:
                normalized_fields.append(normalized_field)
    return normalized_fields or None


def validate_requested_fields(
    fields: list[str] | None,
    model: type[PydanticBaseModel],
) -> list[str] | None:
    """Validate response field selectors against a response model."""
    normalized_fields = split_requested_fields(fields)
    if not normalized_fields:
        return None

    valid_fields = set(model.model_fields) | set(getattr(model, "model_computed_fields", {}))
    invalid_fields = sorted(set(normalized_fields) - valid_fields)
    if invalid_fields:
        valid_field_list = ", ".join(sorted(valid_fields))
        invalid_field_list = ", ".join(invalid_fields)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown field selector(s): {invalid_field_list}. Valid fields: {valid_field_list}",
        )
    return normalized_fields


def dump_selected_fields(
    value: Any,
    model: type[PydanticBaseModel],
    fields: list[str],
) -> dict[str, Any]:
    """Serialize a response object and keep only the requested top-level fields."""
    return model.model_validate(value).model_dump(mode="json", include=set(fields))


def build_selective_json_response(
    value: Any,
    model: type[PydanticBaseModel],
    fields: list[str] | None,
) -> JSONResponse | None:
    """Build a JSON response for partial field selection when requested."""
    validated_fields = validate_requested_fields(fields, model)
    if not validated_fields:
        return None
    return JSONResponse(content=dump_selected_fields(value, model, validated_fields))


def dump_selected_collection(
    values: Iterable[Any],
    model: type[PydanticBaseModel],
    fields: list[str],
) -> list[dict[str, Any]]:
    """Serialize a collection of response objects with top-level field selection."""
    return [dump_selected_fields(value, model, fields) for value in values]


def build_selective_collection_response(
    values: Iterable[Any],
    item_model: type[PydanticBaseModel],
    wrapper_payload: dict[str, Any],
    fields: list[str] | None,
) -> JSONResponse | None:
    """Build a JSON response for a collection with selective item fields."""
    validated_fields = validate_requested_fields(fields, item_model)
    if not validated_fields:
        return None
    payload = dict(wrapper_payload)
    collection_key = next(
        key for key, value in payload.items() if isinstance(value, Iterable) and not isinstance(value, str)
    )
    payload[collection_key] = dump_selected_collection(values, item_model, validated_fields)
    return JSONResponse(content=payload)


class OrmClause(Generic[T], ABC):
    """
    Base class for filtering clauses with paginated_select.

    The subclasses should implement the `to_orm` method and set the `value` attribute.
    """

    def __init__(self, value: T | None = None):
        self.value = value

    @abstractmethod
    def to_orm(self, select: Select) -> Select:
        pass
