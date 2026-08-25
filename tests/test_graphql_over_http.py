from __future__ import annotations

from typing import Any

import pytest

from mocket.plugins.httpretty import HTTPretty

from aiographql.client import GraphQLClient
from aiographql.client import GraphQLRequest
from aiographql.client import GraphQLResponse
from aiographql.client.exceptions import GraphQLRequestException
from aiographql.client.serializer import DefaultSerializer
from aiographql.client.transport.aiohttp import AiohttpTransport
from aiographql.client.transport.base import GRAPHQL_RESPONSE_MEDIA_TYPE
from aiographql.client.transport.base import is_graphql_response
from aiographql.client.transport.base import prepare_get_params
from aiographql.client.transport.httpx import HttpxTransport


def test_prepare_get_params_query_only() -> None:
    serializer = DefaultSerializer()
    req = GraphQLRequest(query="{ hello }")
    params = prepare_get_params(req, serializer)
    assert params == {"query": "{ hello }"}


def test_prepare_get_params_all_fields() -> None:
    serializer = DefaultSerializer()
    req = GraphQLRequest(
        query="query GetUser($active: Boolean!, $limit: Int!) { user(active: $active, limit: $limit) { id } }",
        operation="GetUser",
        variables={"active": True, "limit": 10},
        extensions={"persistedQuery": {"version": 1, "sha256Hash": "abc"}},
    )
    params = prepare_get_params(req, serializer)
    assert params["query"] == req.query
    assert params["operationName"] == "GetUser"
    assert serializer.loads(params["variables"]) == {"active": True, "limit": 10}
    assert serializer.loads(params["extensions"]) == {
        "persistedQuery": {"version": 1, "sha256Hash": "abc"}
    }


def test_prepare_get_params_omits_empty() -> None:
    serializer = DefaultSerializer()
    req = GraphQLRequest(
        query="{ test }",
        variables={},
        extensions={},
    )
    params = prepare_get_params(req, serializer)
    assert params == {"query": "{ test }"}
    assert "variables" not in params
    assert "extensions" not in params
    assert "operationName" not in params


def test_is_graphql_response() -> None:
    # 2xx is always accepted
    assert is_graphql_response(200, "application/json", {"data": {"hello": "world"}})
    assert is_graphql_response(
        200, "application/graphql-response+json", {"data": {"hello": "world"}}
    )

    # 4xx / 5xx with application/graphql-response+json
    assert is_graphql_response(
        400,
        GRAPHQL_RESPONSE_MEDIA_TYPE,
        {"errors": [{"message": "Syntax error"}]},
    )
    assert is_graphql_response(
        422,
        f"{GRAPHQL_RESPONSE_MEDIA_TYPE}; charset=utf-8",
        {"errors": [{"message": "Unprocessable"}]},
    )
    assert is_graphql_response(
        400,
        GRAPHQL_RESPONSE_MEDIA_TYPE,
        {"data": None, "errors": [{"message": "Error"}]},
    )

    # 4xx with application/json or HTML should NOT be treated as a GraphQL execution response
    assert not is_graphql_response(
        400, "application/json", {"errors": [{"message": "Bad request"}]}
    )
    assert not is_graphql_response(404, "text/html", "Not Found")
    assert not is_graphql_response(500, "text/html", "Internal Server Error")
    assert not is_graphql_response(400, GRAPHQL_RESPONSE_MEDIA_TYPE, None)
    assert not is_graphql_response(400, GRAPHQL_RESPONSE_MEDIA_TYPE, "invalid body")
    assert not is_graphql_response(
        500, GRAPHQL_RESPONSE_MEDIA_TYPE, {"errors": "Internal failure"}
    )
    assert not is_graphql_response(
        400, GRAPHQL_RESPONSE_MEDIA_TYPE, {"errors": ["not a dict"]}
    )
    assert not is_graphql_response(
        400, GRAPHQL_RESPONSE_MEDIA_TYPE, {"data": "not a dict or null"}
    )
    assert not is_graphql_response(
        400, GRAPHQL_RESPONSE_MEDIA_TYPE, {"unexpected": "structure"}
    )


@pytest.mark.aiohttp
@pytest.mark.asyncio
async def test_aiohttp_transport_400_graphql_response(
    mocket: Any, httpretty: Any
) -> None:
    endpoint = "http://test.com/graphql"
    transport = AiohttpTransport(endpoint=endpoint)
    request = GraphQLRequest(query="{ invalid }")
    serializer = DefaultSerializer()

    httpretty.register_uri(
        HTTPretty.POST,
        endpoint,
        body='{"errors": [{"message": "Cannot query field invalid"}]}',
        status=400,
        content_type=GRAPHQL_RESPONSE_MEDIA_TYPE,
    )

    response = await transport.request("POST", request, serializer)
    assert isinstance(response, GraphQLResponse)
    assert len(response.errors) == 1
    assert response.errors[0].message == "Cannot query field invalid"


@pytest.mark.httpx
@pytest.mark.asyncio
async def test_httpx_transport_400_graphql_response(
    mocket: Any, httpretty: Any
) -> None:
    endpoint = "http://test.com/graphql"
    transport = HttpxTransport(endpoint=endpoint)
    request = GraphQLRequest(query="{ invalid }")
    serializer = DefaultSerializer()

    httpretty.register_uri(
        HTTPretty.POST,
        endpoint,
        body='{"errors": [{"message": "Cannot query field invalid"}]}',
        status=400,
        content_type=GRAPHQL_RESPONSE_MEDIA_TYPE,
    )

    response = await transport.request("POST", request, serializer)
    assert isinstance(response, GraphQLResponse)
    assert len(response.errors) == 1
    assert response.errors[0].message == "Cannot query field invalid"


@pytest.mark.aiohttp
@pytest.mark.asyncio
async def test_aiohttp_transport_400_legacy_json_raises(
    mocket: Any, httpretty: Any
) -> None:
    endpoint = "http://test.com/graphql"
    transport = AiohttpTransport(endpoint=endpoint)
    request = GraphQLRequest(query="{ invalid }")
    serializer = DefaultSerializer()

    httpretty.register_uri(
        HTTPretty.POST,
        endpoint,
        body='{"errors": [{"message": "Bad Request"}]}',
        status=400,
        content_type="application/json",
    )

    with pytest.raises(GraphQLRequestException) as excinfo:
        await transport.request("POST", request, serializer)
    assert excinfo.value.response.json == {"errors": [{"message": "Bad Request"}]}


@pytest.mark.asyncio
async def test_client_query_with_extensions(mocket: Any, httpretty: Any) -> None:
    endpoint = "http://test.com/graphql"
    httpretty.register_uri(
        HTTPretty.POST,
        endpoint,
        body='{"data": {"hello": "world"}}',
        status=200,
        content_type=GRAPHQL_RESPONSE_MEDIA_TYPE,
    )

    client = GraphQLClient(endpoint=endpoint, validate=False)
    response = await client.query(
        request="{ hello }",
        extensions={"persistedQuery": {"version": 1}},
    )
    assert response.data == {"hello": "world"}
    assert isinstance(response.request, GraphQLRequest)
    assert response.request.extensions == {"persistedQuery": {"version": 1}}


@pytest.mark.asyncio
async def test_client_get_with_extensions(mocket: Any, httpretty: Any) -> None:
    endpoint = "http://test.com/graphql"
    httpretty.register_uri(
        HTTPretty.GET,
        endpoint,
        body='{"data": {"hello": "world"}}',
        status=200,
        content_type=GRAPHQL_RESPONSE_MEDIA_TYPE,
    )

    client = GraphQLClient(endpoint=endpoint, validate=False)
    response = await client.get(
        request=GraphQLRequest(query="{ hello }"),
        extensions={"persistedQuery": {"version": 1}},
    )
    assert response.data == {"hello": "world"}
    assert isinstance(response.request, GraphQLRequest)
    assert response.request.extensions == {"persistedQuery": {"version": 1}}


@pytest.mark.asyncio
async def test_client_post_with_extensions(mocket: Any, httpretty: Any) -> None:
    endpoint = "http://test.com/graphql"
    httpretty.register_uri(
        HTTPretty.POST,
        endpoint,
        body='{"data": {"hello": "world"}}',
        status=200,
        content_type=GRAPHQL_RESPONSE_MEDIA_TYPE,
    )

    client = GraphQLClient(endpoint=endpoint, validate=False)
    response = await client.post(
        request=GraphQLRequest(query="{ hello }"),
        extensions={"persistedQuery": {"version": 1}},
    )
    assert response.data == {"hello": "world"}
    assert isinstance(response.request, GraphQLRequest)
    assert response.request.extensions == {"persistedQuery": {"version": 1}}


@pytest.mark.httpx
@pytest.mark.asyncio
async def test_httpx_transport_400_legacy_json_raises(
    mocket: Any, httpretty: Any
) -> None:
    endpoint = "http://test.com/graphql"
    transport = HttpxTransport(endpoint=endpoint)
    request = GraphQLRequest(query="{ invalid }")
    serializer = DefaultSerializer()

    httpretty.register_uri(
        HTTPretty.POST,
        endpoint,
        body='{"errors": [{"message": "Bad Request"}]}',
        status=400,
        content_type="application/json",
    )

    with pytest.raises(GraphQLRequestException) as excinfo:
        await transport.request("POST", request, serializer)
    assert excinfo.value.response.json == {"errors": [{"message": "Bad Request"}]}
