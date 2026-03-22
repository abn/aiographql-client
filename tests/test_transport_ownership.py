from __future__ import annotations

from typing import TYPE_CHECKING
from typing import cast
from unittest.mock import patch

import pytest

from aiographql.client import GraphQLClient


if TYPE_CHECKING:
    from aiographql.client.transport.aiohttp import AiohttpTransport
    from aiographql.client.transport.httpx import HttpxTransport

pytestmark = pytest.mark.asyncio


@pytest.mark.aiohttp
async def test_user_ownership_aiohttp(server: str, query_city: str) -> None:
    import aiohttp

    """
    Test that user-provided aiohttp.ClientSession is not closed by the client.
    """
    async with aiohttp.ClientSession() as session:
        client = GraphQLClient(endpoint=server, session=session, validate=False)
        await client.query(query_city)
        await client.close()

        assert not session.closed


@pytest.mark.httpx
async def test_user_ownership_httpx(server: str, query_city: str) -> None:
    import httpx

    """
    Test that user-provided httpx.AsyncClient is not closed by the client.
    """
    async with httpx.AsyncClient() as httpx_client:
        client = GraphQLClient(
            endpoint=server,
            session=httpx_client,
            validate=False,
        )
        await client.query(query_city)
        await client.close()

        assert not httpx_client.is_closed


@pytest.mark.aiohttp
async def test_library_ownership_aiohttp(server: str, query_city: str) -> None:
    """
    Test that library-created aiohttp session is closed by the client.
    """
    with patch(
        "aiographql.client.transport.resolver._is_httpx_available", return_value=False
    ):
        client = GraphQLClient(endpoint=server, validate=False)
    await client.query(query_city)

    # Access internal session
    transport = cast("AiohttpTransport", client._transport)
    session = transport._session
    assert session is not None
    assert not session.closed

    await client.close()
    assert session.closed


@pytest.mark.httpx
async def test_library_ownership_httpx(server: str, query_city: str) -> None:
    """
    Test that library-created httpx client is closed by the client.
    """
    with patch(
        "aiographql.client.transport.resolver._is_aiohttp_available", return_value=False
    ):
        client = GraphQLClient(endpoint=server, validate=False)
    await client.query(query_city)

    # Access internal client
    transport = cast("HttpxTransport", client._transport)
    httpx_client = transport._client
    assert httpx_client is not None
    assert not httpx_client.is_closed

    await client.close()
    assert httpx_client.is_closed


@pytest.mark.aiohttp
async def test_connection_pooling_aiohttp(server: str, query_city: str) -> None:
    """
    Test that multiple queries reuse the same session instance.
    """
    with patch(
        "aiographql.client.transport.resolver._is_httpx_available", return_value=False
    ):
        client = GraphQLClient(endpoint=server, validate=False)

    await client.query(query_city)
    transport = cast("AiohttpTransport", client._transport)
    session1 = transport._session

    await client.query(query_city)
    session2 = transport._session

    assert session1 is session2
    assert session1 is not None

    await client.close()


@pytest.mark.httpx
async def test_connection_pooling_httpx(server: str, query_city: str) -> None:
    """
    Test that multiple queries reuse the same httpx client instance.
    """
    with patch(
        "aiographql.client.transport.resolver._is_aiohttp_available", return_value=False
    ):
        client = GraphQLClient(endpoint=server, validate=False)

    await client.query(query_city)
    transport = cast("HttpxTransport", client._transport)
    client1 = transport._client

    await client.query(query_city)
    client2 = transport._client

    assert client1 is client2
    assert client1 is not None

    await client.close()
