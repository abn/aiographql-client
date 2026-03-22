from __future__ import annotations

from typing import Any
from unittest.mock import patch

import pytest

from mocket.plugins.httpretty import HTTPretty

from aiographql.client.exceptions import GraphQLClientException
from aiographql.client.exceptions import GraphQLRequestException
from aiographql.client.request import GraphQLRequest
from aiographql.client.response import GraphQLResponse
from aiographql.client.serializer import DefaultSerializer
from aiographql.client.transport import HttpxTransport


pytestmark = [pytest.mark.httpx, pytest.mark.strawberry]


@pytest.mark.asyncio
async def test_httpx_transport_post_success(
    mocket: Any, httpretty: Any, strawberry_server: str
) -> None:
    endpoint = strawberry_server
    transport = HttpxTransport(endpoint=endpoint)
    serializer = DefaultSerializer()
    request = GraphQLRequest(
        query="{ hello }", headers={"Content-Type": "application/json"}
    )

    httpretty.register_uri(
        HTTPretty.POST,
        endpoint,
        body='{"data": {"hello": "world"}}',
        content_type="application/json",
    )

    response = await transport.request(
        method="post", request=request, serializer=serializer
    )

    assert isinstance(response, GraphQLResponse)
    assert response.data == {"hello": "world"}


@pytest.mark.asyncio
async def test_httpx_transport_get_success(
    mocket: Any, httpretty: Any, strawberry_server: str
) -> None:
    endpoint = strawberry_server
    transport = HttpxTransport(endpoint=endpoint)
    serializer = DefaultSerializer()
    request = GraphQLRequest(
        query="{ hello }", headers={"Content-Type": "application/json"}
    )

    httpretty.register_uri(
        HTTPretty.GET,
        endpoint,
        body='{"data": {"hello": "world"}}',
        content_type="application/json",
    )

    response = await transport.request(
        method="get", request=request, serializer=serializer
    )

    assert response.data == {"hello": "world"}


@pytest.mark.asyncio
async def test_httpx_transport_non_200_raises_exception(
    strawberry_server: str,
) -> None:
    endpoint = f"{strawberry_server}/not-found"
    transport = HttpxTransport(endpoint=endpoint)
    serializer = DefaultSerializer()
    request = GraphQLRequest(query="{ hello }")

    with pytest.raises(GraphQLRequestException) as excinfo:
        await transport.request(method="POST", request=request, serializer=serializer)

    assert excinfo.value.response.json == {}


@pytest.mark.asyncio
async def test_httpx_transport_invalid_json_response(
    mocket: Any, httpretty: Any, strawberry_server: str
) -> None:
    endpoint = strawberry_server
    transport = HttpxTransport(endpoint=endpoint)
    serializer = DefaultSerializer()
    request = GraphQLRequest(query="{ hello }")

    httpretty.register_uri(
        HTTPretty.POST,
        endpoint,
        body="invalid json",
        content_type="text/plain",
        status=200,
    )

    # This test ensures that when the response body is not valid JSON,
    # GraphQLResponse.json is None.

    response = await transport.request(
        method="POST", request=request, serializer=serializer
    )
    assert response.json == {}


@pytest.mark.asyncio
async def test_httpx_transport_http_error(mocket: Any, strawberry_server: str) -> None:
    endpoint = strawberry_server
    transport = HttpxTransport(endpoint=endpoint)
    serializer = DefaultSerializer()
    request = GraphQLRequest(query="{ hello }")

    from mocket.socket import MocketSocket

    def side_effect(*args: Any, **kwargs: Any) -> None:
        raise ConnectionRefusedError("Connection refused")

    with (
        patch.object(MocketSocket, "connect", side_effect=side_effect),
        pytest.raises(GraphQLClientException) as excinfo,
    ):
        await transport.request(method="POST", request=request, serializer=serializer)
    assert "HTTP request failed" in str(excinfo.value)


@pytest.mark.asyncio
async def test_httpx_transport_external_client(strawberry_server: str) -> None:
    endpoint = strawberry_server
    import httpx

    async with httpx.AsyncClient() as client:
        transport = HttpxTransport(endpoint=endpoint, client=client)
        serializer = DefaultSerializer()
        request = GraphQLRequest(
            query="{ hello }", headers={"Content-Type": "application/json"}
        )

        response = await transport.request(
            method="POST", request=request, serializer=serializer
        )
        assert response.data == {"hello": "world"}

        await transport.close()
        # httpx client should NOT be closed if it was provided by the user
        assert not client.is_closed


@pytest.mark.asyncio
async def test_httpx_transport_invalid_method() -> None:
    transport = HttpxTransport(endpoint="http://example.com")
    with pytest.raises(GraphQLClientException) as excinfo:
        await transport.request(
            method="PUT",
            request=GraphQLRequest(query="{ hello }"),
            serializer=DefaultSerializer(),
        )
    assert "Invalid method (PUT) specified" in str(excinfo.value)


@pytest.mark.asyncio
async def test_httpx_transport_http_error_handling(mocket: Any, httpretty: Any) -> None:
    endpoint = "http://test.com/graphql"
    transport = HttpxTransport(endpoint=endpoint)
    request = GraphQLRequest(query="{ test }")
    serializer = DefaultSerializer()

    # Simulate a generic HTTPError by forcing a connection failure via mocket
    from mocket.socket import MocketSocket

    def side_effect(*args: Any, **kwargs: Any) -> None:
        raise ConnectionRefusedError("Connection refused")

    with (
        patch.object(MocketSocket, "connect", side_effect=side_effect),
        pytest.raises(GraphQLClientException, match="HTTP request failed"),
    ):
        await transport.request("POST", request, serializer)


@pytest.mark.asyncio
async def test_httpx_transport_status_error_handling(
    mocket: Any, httpretty: Any
) -> None:
    endpoint = "http://test.com/graphql"
    transport = HttpxTransport(endpoint=endpoint)
    request = GraphQLRequest(query="{ test }")
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
async def test_httpx_transport_coerce_value_async() -> None:
    transport = HttpxTransport(endpoint="http://test.com")
    serializer = DefaultSerializer()

    assert transport._coerce_value(True, serializer) == 1
    assert transport._coerce_value({"a": 1}, serializer) == '{"a":1}'


@pytest.mark.asyncio
async def test_httpx_transport_invalid_method_async() -> None:
    transport = HttpxTransport(endpoint="http://test")
    with pytest.raises(GraphQLClientException, match="Invalid method"):
        await transport.request(
            "INVALID", GraphQLRequest(query="{test}"), DefaultSerializer()
        )
