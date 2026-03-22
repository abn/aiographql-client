from __future__ import annotations

import asyncio
import gc

from typing import TYPE_CHECKING
from typing import Any
from unittest.mock import AsyncMock
from unittest.mock import patch

import pytest

from aiographql.client import GraphQLClient
from aiographql.client import GraphQLRequest
from aiographql.client.exceptions import GraphQLClientException


pytestmark = pytest.mark.asyncio


if TYPE_CHECKING:
    from collections.abc import AsyncGenerator


@pytest.fixture
async def event_loop_exceptions() -> AsyncGenerator[
    list[tuple[None, dict[str, Any]]], None
]:
    running_loop = asyncio.get_running_loop()
    exceptions: list[tuple[None, dict[str, Any]]] = []

    def exception_handler(_: Any, context: dict[str, Any]) -> None:
        nonlocal exceptions
        exceptions.append((None, context))

    old_handler = running_loop.get_exception_handler()
    running_loop.set_exception_handler(exception_handler)

    yield exceptions

    running_loop.set_exception_handler(old_handler)


async def test_helper_implicit_aiohttp_client_session_is_closed(
    event_loop_exceptions: list[tuple[None, dict[str, Any]]],
    client: GraphQLClient,
    headers: dict[str, str],
    query_city: str,
) -> None:
    try:
        from aiographql.client.transport.aiohttp import AiohttpTransport
        from aiographql.client.transport.aiohttp import AiohttpTransport as _

        if not isinstance(client.transport, AiohttpTransport):
            pytest.skip("client not using aiohttp")
    except ImportError:
        pytest.skip("aiohttp not installed")

    request = GraphQLRequest(query=query_city, headers=headers)
    await client.query(request)

    # force python to gc unclosed sessions
    gc.collect()

    for _, context in event_loop_exceptions:
        # we check the message and that it is not related to any persistent session
        if context["message"] == "Unclosed client session":
            pytest.fail(f"Found unclosed client session: {context}")


async def test_client_closes_internal_transport_on_exit() -> None:
    endpoint = "http://example.com/graphql"
    client = GraphQLClient(endpoint=endpoint)
    transport = client.transport

    # Mock the close method of the transport
    with patch.object(transport, "close", new_callable=AsyncMock) as mock_close:
        async with client:
            pass

        mock_close.assert_called_once()


async def test_ownership_external_aiohttp() -> None:
    try:
        import aiohttp as _  # noqa: F401
    except ImportError:
        pytest.skip("aiohttp not installed")

    import aiohttp

    """
    User-provided aiohttp.ClientSession instances are not closed by the library.
    """
    endpoint = "http://example.com/graphql"
    session = aiohttp.ClientSession()
    try:
        client = GraphQLClient(endpoint=endpoint, session=session)
        async with client:
            pass
        assert not session.closed
    finally:
        await session.close()


@pytest.mark.httpx
async def test_ownership_external_httpx() -> None:
    import httpx

    """
    User-provided httpx.AsyncClient instances are not closed by the library.
    """
    endpoint = "http://example.com/graphql"
    client_httpx = httpx.AsyncClient()
    try:
        client = GraphQLClient(endpoint=endpoint, session=client_httpx)
        async with client:
            pass
        assert not client_httpx.is_closed
    finally:
        await client_httpx.aclose()


@pytest.mark.aiohttp
async def test_ownership_internal_aiohttp() -> None:
    from aiographql.client.transport.aiohttp import AiohttpTransport

    """
    Internally created aiohttp sessions are closed exactly once.
    """

    endpoint = "http://example.com/graphql"
    with patch(
        "aiographql.client.transport.resolver._is_httpx_available", return_value=False
    ):
        client = GraphQLClient(endpoint=endpoint)
    transport = client.transport
    assert isinstance(transport, AiohttpTransport)

    # Trigger session creation
    session = await transport._get_session()
    assert transport._owns_session is True

    with patch.object(session, "close", wraps=session.close) as mock_close:
        await client.close()
        mock_close.assert_called_once()

    assert session.closed


@pytest.mark.httpx
async def test_ownership_internal_httpx() -> None:
    from aiographql.client.transport.httpx import HttpxTransport

    """
    Internally created httpx clients are closed exactly once.
    """

    endpoint = "http://example.com/graphql"
    with patch(
        "aiographql.client.transport.resolver._is_aiohttp_available", return_value=False
    ):
        client = GraphQLClient(endpoint=endpoint)
    transport = client.transport
    assert isinstance(transport, HttpxTransport)

    # Trigger client creation
    httpx_client = await transport._get_client()
    assert transport._owns_client is True

    with patch.object(httpx_client, "aclose", wraps=httpx_client.aclose) as mock_close:
        await client.close()
        mock_close.assert_called_once()

    assert httpx_client.is_closed


async def test_subscription_internal_session_cleanup() -> None:
    try:
        from aiographql.client.transport.aiohttp import AiohttpSubscriptionTransport

        # When GraphQLClient.subscribe is called without a session, it passes None to get_default_subscription_transport
        # which creates AiohttpSubscriptionTransport(session=None).
        transport = AiohttpSubscriptionTransport(endpoint="http://example.com/graphql")
    except (ImportError, GraphQLClientException):
        pytest.skip("aiohttp not installed or not available")

    """
    Verify that an internally created session for a subscription is cleaned up when the subscription transport is closed.
    """

    session = await transport._get_session()
    assert transport._owns_session is True

    with patch.object(session, "close", wraps=session.close) as mock_close:
        await transport.close()
        mock_close.assert_called_once()

    assert session.closed


async def test_no_unclosed_session_warnings(recwarn: pytest.WarningsRecorder) -> None:
    """
    Run a simple client lifecycle and check for ResourceWarning related to unclosed sessions.
    """
    endpoint = "http://example.com/graphql"

    # We'll use a real-ish but unreachable endpoint to avoid actual network but trigger session usage if needed.
    # Actually, just open and close is enough for transport.
    async with GraphQLClient(endpoint=endpoint) as client:
        # Just to be sure the session is created if it's aiohttp
        try:
            from aiographql.client.transport.aiohttp import AiohttpTransport

            if isinstance(client.transport, AiohttpTransport):
                await client.transport._get_session()
        except ImportError:
            pass

        try:
            from aiographql.client.transport.httpx import HttpxTransport

            if isinstance(client.transport, HttpxTransport):
                await client.transport._get_client()
        except ImportError:
            pass

    # Filter for ResourceWarnings
    resource_warnings = [w for w in recwarn if issubclass(w.category, ResourceWarning)]
    # aiohttp sometimes emits warnings about unclosed connectors even if session is closed,
    # but we want to make sure WE didn't leave a session open.
    for w in resource_warnings:
        assert "unclosed" not in str(w.message).lower()
