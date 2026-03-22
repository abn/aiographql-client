from __future__ import annotations

import asyncio
import gc

from typing import TYPE_CHECKING
from typing import Any
from unittest.mock import patch

import pytest

from aiographql.client import GraphQLClient


if TYPE_CHECKING:
    from collections.abc import AsyncGenerator


pytestmark = pytest.mark.asyncio


@pytest.fixture
async def event_loop_exceptions() -> AsyncGenerator[list[dict[str, Any]], None]:
    running_loop = asyncio.get_running_loop()
    exceptions: list[dict[str, Any]] = []

    def exception_handler(_: Any, context: dict[str, Any]) -> None:
        exceptions.append(context)

    old_handler = running_loop.get_exception_handler()
    running_loop.set_exception_handler(exception_handler)

    yield exceptions

    running_loop.set_exception_handler(old_handler)


@pytest.mark.aiohttp
async def test_user_ownership_aiohttp(server: str, query_city: str) -> None:
    import aiohttp

    """
    User Ownership Test: User-provided aiohttp.ClientSession is NOT closed.
    """
    async with aiohttp.ClientSession() as session:
        client = GraphQLClient(endpoint=server, session=session, validate=False)
        await client.query(query_city)
        await client.close()

        assert not session.closed

    assert session.closed


@pytest.mark.httpx
async def test_user_ownership_httpx(server: str, query_city: str) -> None:
    import httpx

    """
    User Ownership Test: User-provided httpx.AsyncClient is NOT closed.
    """
    async with httpx.AsyncClient() as session:
        client = GraphQLClient(
            endpoint=server,
            session=session,
            validate=False,
        )
        await client.query(query_city)
        await client.close()

        assert not session.is_closed

    assert session.is_closed


@pytest.mark.aiohttp
async def test_library_ownership_aiohttp(
    server: str, query_city: str, event_loop_exceptions: list[dict[str, Any]]
) -> None:
    import aiohttp

    """
    Library Ownership Test: Library-created sessions ARE closed safely.
    """
    with patch(
        "aiographql.client.transport.resolver._is_httpx_available", return_value=False
    ):
        client = GraphQLClient(endpoint=server, validate=False)
    await client.query(query_city)

    internal_session = client._session()
    assert isinstance(internal_session, aiohttp.ClientSession)
    assert not internal_session.closed

    await client.close()
    assert internal_session.closed

    # Force GC to check for unclosed session warnings
    gc.collect()
    await asyncio.sleep(0)

    for context in event_loop_exceptions:
        if context.get("message") == "Unclosed client session":
            pytest.fail(f"Found unclosed client session: {context}")


@pytest.mark.httpx
async def test_library_ownership_httpx(server: str, query_city: str) -> None:
    import httpx

    """
    Library Ownership Test: Library-created httpx clients ARE closed safely.
    """
    with patch(
        "aiographql.client.transport.resolver._is_aiohttp_available", return_value=False
    ):
        client = GraphQLClient(endpoint=server, validate=False)
    await client.query(query_city)

    internal_client = client._session()
    assert isinstance(internal_client, httpx.AsyncClient)
    assert not internal_client.is_closed

    await client.close()
    assert internal_client.is_closed


@pytest.mark.aiohttp
async def test_connection_pooling_aiohttp(server: str, query_city: str) -> None:
    import aiohttp

    """
    Connection Pooling Test: Consecutive calls reuse the same internal session.
    """
    with patch(
        "aiographql.client.transport.resolver._is_httpx_available", return_value=False
    ):
        client = GraphQLClient(endpoint=server, validate=False)
    await client.query(query_city)
    session1 = client._session()

    await client.query(query_city)
    session2 = client._session()

    assert session1 is session2
    assert isinstance(session1, aiohttp.ClientSession)

    await client.close()


@pytest.mark.httpx
async def test_connection_pooling_httpx(server: str, query_city: str) -> None:
    import httpx

    """
    Connection Pooling Test: Consecutive calls reuse the same internal httpx client.
    """
    with patch(
        "aiographql.client.transport.resolver._is_aiohttp_available", return_value=False
    ):
        client = GraphQLClient(endpoint=server, validate=False)
    await client.query(query_city)
    client1 = client._session()

    await client.query(query_city)
    client2 = client._session()

    assert client1 is client2
    assert isinstance(client1, httpx.AsyncClient)

    await client.close()


@pytest.mark.aiohttp
async def test_explicit_session_override(server: str, query_city: str) -> None:
    import aiohttp

    """
    Verify that providing a session to the query method overrides the client's default.
    """
    client = GraphQLClient(endpoint=server, validate=False)

    async with aiohttp.ClientSession() as override_session:
        await client.query(query_city, session=override_session)
        # The internal session should still be None or different
        assert client._session() is not override_session

        # If it was lazy loaded
        if client._session() is not None:
            assert client._session() is not override_session

    await client.close()
