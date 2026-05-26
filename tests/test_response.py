from __future__ import annotations

import pytest

from aiographql.client.response import GraphQLResponse


def test_graphql_response_data_fallback() -> None:
    # If data is None in json, it should fallback to {}
    response = GraphQLResponse(request="...", json={"data": None})
    assert response.data == {}


def test_graphql_response_errors_fallback() -> None:
    # If errors is None or missing, it should return []
    response = GraphQLResponse(request="...", json={"errors": None})
    assert response.errors == []

    response_no_errors_key = GraphQLResponse(request="...", json={})
    assert response_no_errors_key.errors == []

    # Valid errors
    response_with_errors = GraphQLResponse(
        request="...",
        json={"errors": [{"message": "Bad error", "extensions": {"code": "500"}}]},
    )
    assert len(response_with_errors.errors) == 1
    assert response_with_errors.errors[0].message == "Bad error"


def test_graphql_response_coverage() -> None:
    # Test query property when request is a string
    # We need to bypass GraphQLRequestContainer.__post_init__ to have request as str
    response = GraphQLResponse(
        request="{ city { name } }", json={"data": {"city": {"name": "Test"}}}
    )
    object.__setattr__(response, "request", "{ city { name } }")
    assert response.query == "{ city { name } }"

    # Test query property when request is a GraphQLRequest
    from aiographql.client.request import GraphQLRequest

    request_obj = GraphQLRequest(query="{ a { b } }")
    response_with_obj = GraphQLResponse(request=request_obj, json={})
    assert response_with_obj.query == "{ a { b } }"

    # Test data_as with path navigation and ValueError
    response_invalid_data = GraphQLResponse(
        request="...", json={"data": {"city": "NotADict"}}
    )
    with pytest.raises(ValueError, match=r"Cannot navigate to city\.name in"):
        response_invalid_data.data_as(str, path="city.name")

    # Correct path navigation
    response_with_data = GraphQLResponse(
        request="...", json={"data": {"a": {"b": "c"}}}
    )
    val = response_with_data.data_as(str, path="a.b")
    assert val == "c"

    # data_as without path
    val2 = response_with_data.data_as(dict)
    assert val2 == {"a": {"b": "c"}}
