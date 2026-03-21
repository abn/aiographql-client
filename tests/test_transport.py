from __future__ import annotations

from typing import TYPE_CHECKING

import aiohttp
import pytest

from aiographql.client.exceptions import GraphQLRequestException
from aiographql.client.request import GraphQLRequest
from aiographql.client.response import GraphQLResponse
from aiographql.client.serializer import DefaultSerializer
from aiographql.client.transport import AiohttpTransport


if TYPE_CHECKING:
    from pytest_mock import MockerFixture


@pytest.mark.asyncio
async def test_aiohttp_transport_post_success(mocker: MockerFixture) -> None:
    endpoint = "http://example.com/graphql"
    transport = AiohttpTransport(endpoint=endpoint)
    serializer = DefaultSerializer()
    request = GraphQLRequest(query="{ hello }")

    mock_response = mocker.AsyncMock(spec=aiohttp.ClientResponse)
    mock_response.status = 200
    mock_response.read.return_value = b'{"data": {"hello": "world"}}'

    mock_session = mocker.AsyncMock(spec=aiohttp.ClientSession)
    mock_session.request.return_value.__aenter__.return_value = mock_response

    response = await transport.request(
        method="post", request=request, serializer=serializer, session=mock_session
    )

    assert isinstance(response, GraphQLResponse)
    assert response.data == {"hello": "world"}
    mock_session.request.assert_called_once_with(
        method="post",
        url=endpoint,
        headers={},
        data=serializer.dumps(request.payload()),
    )


@pytest.mark.asyncio
async def test_aiohttp_transport_get_success(mocker: MockerFixture) -> None:
    endpoint = "http://example.com/graphql"
    transport = AiohttpTransport(endpoint=endpoint)
    serializer = DefaultSerializer()
    request = GraphQLRequest(query="{ hello }")

    mock_response = mocker.AsyncMock(spec=aiohttp.ClientResponse)
    mock_response.status = 200
    mock_response.read.return_value = b'{"data": {"hello": "world"}}'

    mock_session = mocker.AsyncMock(spec=aiohttp.ClientSession)
    mock_session.request.return_value.__aenter__.return_value = mock_response

    response = await transport.request(
        method="get", request=request, serializer=serializer, session=mock_session
    )

    assert response.data == {"hello": "world"}
    mock_session.request.assert_called_once_with(
        method="get",
        url=endpoint,
        headers={},
        params={"query": "{ hello }", "variables": "{}"},
    )


@pytest.mark.asyncio
async def test_aiohttp_transport_non_200_raises_exception(
    mocker: MockerFixture,
) -> None:
    endpoint = "http://example.com/graphql"
    transport = AiohttpTransport(endpoint=endpoint)
    serializer = DefaultSerializer()
    request = GraphQLRequest(query="{ hello }")

    mock_response = mocker.AsyncMock(spec=aiohttp.ClientResponse)
    mock_response.status = 404
    mock_response.read.return_value = b"Not Found"

    mock_session = mocker.AsyncMock(spec=aiohttp.ClientSession)
    mock_session.request.return_value.__aenter__.return_value = mock_response

    with pytest.raises(GraphQLRequestException) as excinfo:
        await transport.request(
            method="POST", request=request, serializer=serializer, session=mock_session
        )

    assert excinfo.value.response.json is None


@pytest.mark.asyncio
async def test_aiohttp_transport_close_session(mocker: MockerFixture) -> None:
    mock_session = mocker.AsyncMock(spec=aiohttp.ClientSession)
    transport = AiohttpTransport(endpoint="http://example.com", session=mock_session)

    await transport.close()
    mock_session.close.assert_called_once()
