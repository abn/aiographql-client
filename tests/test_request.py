from aiographql.client import GraphQLRequest
from aiographql.client.request import GraphQLRequestContainer


def test_request_container():
    request = GraphQLRequest(query="{}")
    container = GraphQLRequestContainer(request=request)
    assert container.request == request
    assert id(container.request) != id(request)


def test_request_container_init_string():
    request = GraphQLRequest(query="{}")
    # noinspection PyTypeChecker
    container = GraphQLRequestContainer(request="{}")
    assert container.request == request
    assert id(container.request) != id(request)


def test_request_container_overrides():
    request = GraphQLRequest(query="{}")
    headers = {"Authorization": "Bearer token"}
    operation = "operationName"
    variables = {"foo": "bar"}
    container = GraphQLRequestContainer(
        request=request, headers=headers, operation=operation, variables=variables
    )
    assert container.request != request
    assert container.request.headers == headers
    assert container.request.operationName == operation
    assert container.request.variables == variables


def test_request_payload_coerce():
    assert GraphQLRequest._coerce_value(True) == 1
    assert GraphQLRequest._coerce_value({}) == "{}"

    request = GraphQLRequest(query="{}", variables={"foo": "bar", "baz": False})
    assert request.payload(coerce=True) == {
        "query": "{}",
        "variables": '{"foo":"bar","baz":false}',
    }
    assert request.payload(coerce=False) == {
        "query": "{}",
        "variables": {"baz": False, "foo": "bar"},
    }
