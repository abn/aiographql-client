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
        client: GraphQLClient, graphql_request: GraphQLRequest
    ) -> GraphQLResponse:
        response = await client.post(request=graphql_request)
        return response

    yield post_func


@pytest.mark.asyncio
async def test_client_headers(
    server: str,
    headers: dict[str, str],
    post: Callable[[GraphQLClient, GraphQLRequest], Awaitable[GraphQLResponse]],
    query_city: str,
) -> None:
    async with GraphQLClient(endpoint=server, headers=headers) as client:
        graphql_request = GraphQLRequest(query=query_city)
        response = await post(client, graphql_request)
        assert isinstance(response, GraphQLResponse)


@pytest.mark.asyncio
async def test_request_headers(
    server: str,
    headers: dict[str, str],
    post: Callable[[GraphQLClient, GraphQLRequest], Awaitable[GraphQLResponse]],
    query_city: str,
) -> None:
    async with GraphQLClient(endpoint=server) as client:
        graphql_request = GraphQLRequest(query=query_city, headers=headers)
        response = await post(client, graphql_request)
        assert isinstance(response, GraphQLResponse)


@pytest.mark.asyncio
async def test_post_headers(
    server: str, headers: dict[str, str], client: GraphQLClient, query_city: str
) -> None:
    graphql_request = GraphQLRequest(query=query_city)
    response = await client.post(graphql_request, headers=headers)
    assert isinstance(response, GraphQLResponse)
    assert response.data
    assert not response.errors


@pytest.mark.asyncio
async def test_no_headers(server: str, client: GraphQLClient, query_city: str) -> None:
    graphql_request = GraphQLRequest(query=query_city)
    with pytest.raises(GraphQLIntrospectionException):
        await client.post(graphql_request)
