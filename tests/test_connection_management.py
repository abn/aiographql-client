from __future__ import annotations

from unittest.mock import patch

import aiohttp
import httpx
import pytest

from aiographql.client import GraphQLClient
from aiographql.client.transport.http import AiohttpTransport
from aiographql.client.transport.http import HttpxTransport


pytestmark = pytest.mark.asyncio


async def test_aiohttp_user_ownership(
    server: str, query_city: str, headers: dict[str, str]
) -> None:
    """
    Test that user-provided aiohttp.ClientSession is NOT closed by the client.
    """
    async with aiohttp.ClientSession() as session:
        client = GraphQLClient(endpoint=server, session=session, headers=headers)
        await client.query(query_city)
        await client.close()

        assert not session.closed

    assert session.closed  # Should be closed by our context manager


async def test_httpx_user_ownership(
    server: str, query_city: str, headers: dict[str, str]
) -> None:
    """
    Test that user-provided httpx.AsyncClient is NOT closed by the client.
    """
    async with httpx.AsyncClient() as session:
        client = GraphQLClient(endpoint=server, session=session, headers=headers)
        await client.query(query_city)
        await client.close()

        assert not session.is_closed

    assert session.is_closed  # Should be closed by our context manager


async def test_aiohttp_library_ownership(
    server: str, query_city: str, headers: dict[str, str]
) -> None:
    """
    Test that library-created aiohttp sessions ARE closed by the client.
    """
    with patch(
        "aiographql.client.transport.resolver._is_httpx_available", return_value=False
    ):
        client = GraphQLClient(endpoint=server, headers=headers)
    await client.query(query_city)

    transport = client.transport
    assert isinstance(transport, AiohttpTransport)
    session = await transport._get_session()

    assert not session.closed
    await client.close()
    assert session.closed


async def test_httpx_library_ownership(
    server: str, query_city: str, headers: dict[str, str]
) -> None:
    """
    Test that library-created httpx clients ARE closed by the client.
    """
    with patch(
        "aiographql.client.transport.resolver._is_aiohttp_available", return_value=False
    ):
        client = GraphQLClient(endpoint=server, headers=headers)
    await client.query(query_city)

    transport = client.transport
    assert isinstance(transport, HttpxTransport)
    session = await transport._get_client()

    assert not session.is_closed
    await client.close()
    assert session.is_closed


async def test_aiohttp_connection_pooling(
    server: str, query_city: str, headers: dict[str, str]
) -> None:
    """
    Test that consecutive aiohttp calls reuse the same session instance.
    """
    with patch(
        "aiographql.client.transport.resolver._is_httpx_available", return_value=False
    ):
        client = GraphQLClient(endpoint=server, headers=headers)
    try:
        await client.query(query_city)
        transport = client.transport
        assert isinstance(transport, AiohttpTransport)
        session1 = await transport._get_session()

        await client.query(query_city)
        session2 = await transport._get_session()

        assert session1 is session2
    finally:
        await client.close()


async def test_httpx_connection_pooling(
    server: str, query_city: str, headers: dict[str, str]
) -> None:
    """
    Test that consecutive httpx calls reuse the same client instance.
    """
    with patch(
        "aiographql.client.transport.resolver._is_aiohttp_available", return_value=False
    ):
        client = GraphQLClient(endpoint=server, headers=headers)
    try:
        await client.query(query_city)
        transport = client.transport
        assert isinstance(transport, HttpxTransport)
        session1 = await transport._get_client()

        await client.query(query_city)
        session2 = await transport._get_client()

        assert session1 is session2
    finally:
        await client.close()
