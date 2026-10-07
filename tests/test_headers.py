from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from aiographql.client import GraphQLClient
from aiographql.client import GraphQLIntrospectionException
from aiographql.client import GraphQLRequest
from aiographql.client import GraphQLResponse


if TYPE_CHECKING:
    from collections.abc import Awaitable
    from collections.abc import Callable
    from collections.abc import Iterator


pytestmark = pytest.mark.asyncio


@pytest.fixture
def post() -> Iterator[
    Callable[[GraphQLClient, GraphQLRequest], Awaitable[GraphQLResponse]]
]:
    async def post_func(
        client: GraphQLClient, request: GraphQLRequest
    ) -> GraphQLResponse:
        response = await client.post(request=request)
        return response

    yield post_func


async def test_client_headers(
    server: str,
    headers: dict[str, str],
    post: Callable[[GraphQLClient, GraphQLRequest], Awaitable[GraphQLResponse]],
    query_city: str,
) -> None:
    async with GraphQLClient(endpoint=server, headers=headers) as client:
        request = GraphQLRequest(query=query_city)
        response = await post(client, request)
        assert isinstance(response, GraphQLResponse)


async def test_request_headers(
    server: str,
    headers: dict[str, str],
    post: Callable[[GraphQLClient, GraphQLRequest], Awaitable[GraphQLResponse]],
    query_city: str,
) -> None:
    async with GraphQLClient(endpoint=server) as client:
        request = GraphQLRequest(query=query_city, headers=headers)
        response = await post(client, request)
        assert isinstance(response, GraphQLResponse)


async def test_post_headers(
    server: str, headers: dict[str, str], client: GraphQLClient, query_city: str
) -> None:
    request = GraphQLRequest(query=query_city)
    response = await client.post(request, headers=headers)
    assert isinstance(response, GraphQLResponse)
    assert response.data
    assert not response.errors


async def test_no_headers(server: str, client: GraphQLClient, query_city: str) -> None:
    request = GraphQLRequest(query=query_city)
    with pytest.raises(GraphQLIntrospectionException):
        await client.post(request)


async def test_default_client_headers() -> None:
    client = GraphQLClient(endpoint="http://example.com/graphql")
    assert client._headers["Content-Type"] == "application/json"
    assert (
        client._headers["Accept"]
        == "application/graphql-response+json, application/json"
    )
    assert client._headers["Accept-Encoding"] == "gzip"
