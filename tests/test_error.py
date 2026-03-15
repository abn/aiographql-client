from __future__ import annotations

from typing import Any

import pytest

from aiographql.client import GraphQLError


@pytest.fixture
def error_json_extra_fields() -> dict[str, Any]:
    return {
        "extensions": {"some_field": "foobar"},
        "message": "some error",
        "type": "NOT_FOUND",
    }


def test_handles_extra_fields_in_error(
    query_city: str, error_json_extra_fields: dict[str, Any]
) -> None:
    error = GraphQLError.load(error_json_extra_fields)
    assert error.__class__.__name__ == "CustomGraphQLError"
    assert isinstance(error, GraphQLError)
    assert error.message == "some error"
    assert error.extensions == {"some_field": "foobar"}
    assert error.type == "NOT_FOUND"
