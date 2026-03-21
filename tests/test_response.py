from __future__ import annotations

import pytest

from aiographql.client.response import GraphQLResponse


def test_graphql_response_coverage() -> None:
    # Test query property when request is a string
    # We need to bypass GraphQLRequestContainer.__post_init__ to have request as str
    response = GraphQLResponse(
        request="{ city { name } }", json={"data": {"city": {"name": "Test"}}}
    )
    object.__setattr__(response, "request", "{ city { name } }")
    assert response.query == "{ city { name } }"

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
