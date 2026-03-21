from __future__ import annotations

import httpx
import pytest
import respx

from aiographql.client.exceptions import GraphQLClientException
from aiographql.client.exceptions import GraphQLRequestException
from aiographql.client.request import GraphQLRequest
from aiographql.client.response import GraphQLResponse
from aiographql.client.serializer import DefaultSerializer
from aiographql.client.transport import HttpxTransport


@pytest.mark.asyncio
async def test_httpx_transport_post_success() -> None:
    endpoint = "http://example.com/graphql"
    transport = HttpxTransport(endpoint=endpoint)
    serializer = DefaultSerializer()
    request = GraphQLRequest(query="{ hello }")

    with respx.mock:
        respx.post(endpoint).mock(
            return_value=httpx.Response(200, content=b'{"data": {"hello": "world"}}')
        )

        response = await transport.request(
            method="post", request=request, serializer=serializer
        )

        assert isinstance(response, GraphQLResponse)
        assert response.data == {"hello": "world"}
        assert respx.post(endpoint).called


@pytest.mark.asyncio
async def test_httpx_transport_get_success() -> None:
    endpoint = "http://example.com/graphql"
    transport = HttpxTransport(endpoint=endpoint)
    serializer = DefaultSerializer()
    request = GraphQLRequest(query="{ hello }")

    with respx.mock:
        respx.get(endpoint).mock(
            return_value=httpx.Response(200, content=b'{"data": {"hello": "world"}}')
        )

        response = await transport.request(
            method="get", request=request, serializer=serializer
        )

        assert response.data == {"hello": "world"}
        assert respx.get(endpoint).called


@pytest.mark.asyncio
async def test_httpx_transport_non_200_raises_exception() -> None:
    endpoint = "http://example.com/graphql"
    transport = HttpxTransport(endpoint=endpoint)
    serializer = DefaultSerializer()
    request = GraphQLRequest(query="{ hello }")

    with respx.mock:
        respx.post(endpoint).mock(
            return_value=httpx.Response(404, content=b"Not Found")
        )

        with pytest.raises(GraphQLRequestException) as excinfo:
            await transport.request(
                method="POST", request=request, serializer=serializer
            )

        assert excinfo.value.response.json is None


@pytest.mark.asyncio
async def test_httpx_transport_invalid_json_response() -> None:
    endpoint = "http://example.com/graphql"
    transport = HttpxTransport(endpoint=endpoint)
    serializer = DefaultSerializer()
    request = GraphQLRequest(query="{ hello }")

    with respx.mock:
        respx.post(endpoint).mock(
            return_value=httpx.Response(200, content=b"invalid json")
        )

        response = await transport.request(
            method="POST", request=request, serializer=serializer
        )
        assert response.json is None


@pytest.mark.asyncio
async def test_httpx_transport_http_error() -> None:
    endpoint = "http://example.com/graphql"
    transport = HttpxTransport(endpoint=endpoint)
    serializer = DefaultSerializer()
    request = GraphQLRequest(query="{ hello }")

    with respx.mock:
        respx.post(endpoint).side_effect = httpx.ConnectError("Connection failed")

        with pytest.raises(GraphQLClientException) as excinfo:
            await transport.request(
                method="POST", request=request, serializer=serializer
            )

        assert "HTTP request failed" in str(excinfo.value)


@pytest.mark.asyncio
async def test_httpx_transport_external_client() -> None:
    endpoint = "http://example.com/graphql"
    async with httpx.AsyncClient() as client:
        transport = HttpxTransport(endpoint=endpoint, client=client)
        serializer = DefaultSerializer()
        request = GraphQLRequest(query="{ hello }")

        with respx.mock:
            respx.post(endpoint).mock(
                return_value=httpx.Response(
                    200, content=b'{"data": {"hello": "world"}}'
                )
            )

            response = await transport.request(
                method="POST", request=request, serializer=serializer
            )
            assert response.data == {"hello": "world"}

        await transport.close()
        # httpx client should still be usable if we didn't close it, but we did call close()
        # on transport which calls client.aclose()
        assert client.is_closed


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
