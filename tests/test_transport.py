from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from aiographql.client.exceptions import GraphQLRequestException
from aiographql.client.request import GraphQLRequest
from aiographql.client.response import GraphQLResponse
from aiographql.client.serializer import DefaultSerializer
from aiographql.client.transport import AiohttpTransport


pytestmark = [pytest.mark.aiohttp, pytest.mark.strawberry]


if TYPE_CHECKING:
    from pytest_mock import MockerFixture


@pytest.mark.strawberry
@pytest.mark.asyncio
async def test_aiohttp_transport_post_success(strawberry_server: str) -> None:
    endpoint = strawberry_server
    transport = AiohttpTransport(endpoint=endpoint)
    serializer = DefaultSerializer()
    request = GraphQLRequest(
        query="{ hello }", headers={"Content-Type": "application/json"}
    )

    response = await transport.request(
        method="post", request=request, serializer=serializer
    )

    assert isinstance(response, GraphQLResponse)
    assert response.data == {"hello": "world"}


@pytest.mark.strawberry
@pytest.mark.asyncio
async def test_aiohttp_transport_get_success(strawberry_server: str) -> None:
    endpoint = strawberry_server
    transport = AiohttpTransport(endpoint=endpoint)
    serializer = DefaultSerializer()
    request = GraphQLRequest(
        query="{ hello }", headers={"Content-Type": "application/json"}
    )

    response = await transport.request(
        method="get", request=request, serializer=serializer
    )

    assert response.data == {"hello": "world"}


@pytest.mark.strawberry
@pytest.mark.asyncio
async def test_aiohttp_transport_non_200_raises_exception(
    strawberry_server: str,
) -> None:
    endpoint = f"{strawberry_server}/not-found"
    transport = AiohttpTransport(endpoint=endpoint)
    serializer = DefaultSerializer()
    request = GraphQLRequest(query="{ hello }")

    with pytest.raises(GraphQLRequestException) as excinfo:
        await transport.request(method="POST", request=request, serializer=serializer)

    assert excinfo.value.response.json is None


@pytest.mark.asyncio
async def test_aiohttp_transport_close_session_user_owned(
    mocker: MockerFixture,
) -> None:
    import aiohttp

    mock_session = mocker.AsyncMock(spec=aiohttp.ClientSession)
    transport = AiohttpTransport(endpoint="http://example.com", session=mock_session)

    await transport.close()
    # User-provided session should NOT be closed
    mock_session.close.assert_not_called()


@pytest.mark.asyncio
async def test_aiohttp_transport_close_session_library_owned(
    mocker: MockerFixture,
) -> None:
    import aiohttp

    mock_session = mocker.AsyncMock(spec=aiohttp.ClientSession)
    transport = AiohttpTransport(endpoint="http://example.com")
    transport._session = mock_session
    transport._owns_session = True

    await transport.close()
    # Library-owned session SHOULD be closed
    mock_session.close.assert_called_once()
