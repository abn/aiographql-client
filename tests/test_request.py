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


def test_request_container_init_string_overrides() -> None:
    headers = {"Authorization": "Bearer token"}
    operation = "operationName"
    variables = {"foo": "bar"}
    extensions = {"ext": "val"}
    container = GraphQLRequestContainer(
        request="{}",
        headers=headers,
        operation=operation,
        variables=variables,
        extensions=extensions,
    )
    assert isinstance(container.request, GraphQLRequest)
    assert container.request.query == "{}"
    assert container.request.headers == headers
    assert container.request.operationName == operation
    assert container.request.variables == variables
    assert container.request.extensions == extensions


def test_request_container_overrides() -> None:
    request = GraphQLRequest(query="{}")
    headers = {"Authorization": "Bearer token"}
    operation = "operationName"
    variables = {"foo": "bar"}
    extensions = {"ext": "val"}
    container = GraphQLRequestContainer(
        request=request,
        headers=headers,
        operation=operation,
        variables=variables,
        extensions=extensions,
    )
    assert container.request != request
    assert isinstance(container.request, GraphQLRequest)
    assert container.request.headers == headers
    assert container.request.operationName == operation
    assert container.request.variables == variables
    assert container.request.extensions == extensions


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
        "extensions": {},
    }
    assert request.asdict() == expected_dict


def test_graphql_request_getattribute_fallback() -> None:
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

    # Test payload with extensions
    req_ext = GraphQLRequest(
        query="query Q { test }",
        operation="Q",
        variables={"a": 1},
        extensions={"persistedQuery": {"version": 1}},
    )
    assert req_ext.payload() == {
        "query": "query Q { test }",
        "operationName": "Q",
        "variables": {"a": 1},
        "extensions": {"persistedQuery": {"version": 1}},
    }


def test_request_copy_extensions() -> None:
    req = GraphQLRequest(
        query="{ test }",
        extensions={"persistedQuery": {"version": 1}},
    )
    copied = req.copy(extensions={"extra": True})
    assert copied.extensions == {
        "persistedQuery": {"version": 1},
        "extra": True,
    }
