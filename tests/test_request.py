from __future__ import annotations

import pytest

from aiographql.client import GraphQLRequest
from aiographql.client.request import GraphQLRequestContainer


def test_request_container() -> None:
    request = GraphQLRequest(query="{}")
    container = GraphQLRequestContainer(request=request)
    assert container.request == request
    assert id(container.request) != id(request)


def test_request_container_init_string() -> None:
    request = GraphQLRequest(query="{}")
    # noinspection PyTypeChecker
    container = GraphQLRequestContainer(request="{}")
    assert container.request == request
    assert id(container.request) != id(request)


def test_request_container_overrides() -> None:
    request = GraphQLRequest(query="{}")
    headers = {"Authorization": "Bearer token"}
    operation = "operationName"
    variables = {"foo": "bar"}
    container = GraphQLRequestContainer(
        request=request, headers=headers, operation=operation, variables=variables
    )
    assert container.request != request
    assert isinstance(container.request, GraphQLRequest)
    assert container.request.headers == headers
    assert container.request.operationName == operation
    assert container.request.variables == variables


def test_request_payload() -> None:
    request = GraphQLRequest(query="{}")

    request = GraphQLRequest(query="{}", variables={"foo": "bar", "baz": False})
    assert request.payload() == {
        "query": "{}",
        "variables": {"baz": False, "foo": "bar"},
    }


def test_graphql_request_asdict() -> None:
    request = GraphQLRequest(query="{ city { name } }", operation="GetCity")

    # Test property 'operation' via __getattribute__
    assert request.operation == "GetCity"

    # Test asdict
    expected_dict = {
        "query": "{ city { name } }",
        "operationName": "GetCity",
        "variables": {},
    }
    assert request.asdict() == expected_dict


def test_graphql_request_getattr_fallback() -> None:
    request = GraphQLRequest(query="{ city { name } }", operation="GetCity")

    with pytest.raises(AttributeError):
        _ = request.non_existent


def test_request_payload_extra() -> None:
    # Test payload without variables
    req = GraphQLRequest(query="{ test }")
    assert req.payload() == {"query": "{ test }", "variables": {}}

    # Test payload with operation name
    req_op = GraphQLRequest(query="query Q { test }", operation="Q")
    assert req_op.payload()["operationName"] == "Q"
