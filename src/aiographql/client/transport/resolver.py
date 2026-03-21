from __future__ import annotations

import importlib.metadata

from typing import TYPE_CHECKING
from typing import Any
from typing import cast


if TYPE_CHECKING:
    import aiohttp
    import httpx

    from aiographql.client.transport.base import GraphQLSession
    from aiographql.client.transport.base import GraphQLSubscriptionTransport
    from aiographql.client.transport.base import GraphQLTransport


def _is_httpx_available(min_version: str = "0.24.0") -> bool:
    """
    Check if httpx is available and meets the minimum version requirement.
    """
    try:
        import httpx  # noqa: F401

        version = importlib.metadata.version("httpx")
        # Simple version comparison to avoid adding 'packaging' dependency if not present
        # but the project likely has it or we can use a simpler check.
        # Given the environment, let's try to be robust.
        parts = [int(p) for p in version.split(".") if p.isdigit()]
        min_parts = [int(p) for p in min_version.split(".") if p.isdigit()]
        return parts >= min_parts
    except (ImportError, importlib.metadata.PackageNotFoundError, ValueError):
        return False


def _is_aiohttp_available() -> bool:
    """
    Check if aiohttp is available.
    """
    try:
        import aiohttp  # noqa: F401

        return True
    except ImportError:
        return False


def _is_websockets_available() -> bool:
    """
    Check if websockets is available.
    """
    try:
        import websockets  # noqa: F401

        return True
    except ImportError:
        return False


def get_default_transport(
    endpoint: str,
    transport: GraphQLTransport | None = None,
    session: GraphQLSession | None = None,
    client: GraphQLSession | None = None,
    **kwargs: Any,
) -> GraphQLTransport:
    """
    Resolve the transport to use for making GraphQL requests.

    :param endpoint: The GraphQL endpoint URL.
    :param transport: The transport to use. If not provided, the best available
        transport is automatically selected (preferring aiohttp). Must be a
        :class:`GraphQLTransport` instance.
    :param session: An optional `GraphQLSession`.
    :param client: An optional httpx.AsyncClient.
    :param kwargs: Additional arguments to pass to the transport constructor.
    :return: A GraphQLTransport instance.
    :raises ImportError: If the requested transport is not available.
    :raises RuntimeError: If "auto" transport is requested but no suitable transport is
        available.
    """
    if transport is not None:
        return transport

    # auto or None
    _session = client or session
    if _session is not None:
        try:
            import httpx

            if isinstance(_session, httpx.AsyncClient):
                from aiographql.client.transport.httpx import HttpxTransport

                return HttpxTransport(endpoint=endpoint, client=_session, **kwargs)
        except ImportError:
            pass

        try:
            import aiohttp

            if isinstance(_session, aiohttp.ClientSession):
                from aiographql.client.transport.aiohttp import AiohttpTransport

                return AiohttpTransport(endpoint=endpoint, session=_session, **kwargs)
        except ImportError:
            pass

    if _is_aiohttp_available():
        from aiographql.client.transport.aiohttp import AiohttpTransport

        return AiohttpTransport(
            endpoint=endpoint,
            session=cast("aiohttp.ClientSession | None", session),
            **kwargs,
        )

    if _is_httpx_available():
        from aiographql.client.transport.httpx import HttpxTransport

        return HttpxTransport(
            endpoint=endpoint,
            client=cast("httpx.AsyncClient | None", client or session),
            **kwargs,
        )

    raise RuntimeError(
        "No suitable transport found. Please install either `aiohttp` or `httpx>=0.24.0` via extras, "
        "e.g., `pip install aiographql-client[aiohttp]` or `pip install aiographql-client[httpx]`."
    )


def get_default_subscription_transport(
    endpoint: str,
    transport: GraphQLSubscriptionTransport | None = None,
    session: GraphQLSession | None = None,
    **kwargs: Any,
) -> GraphQLSubscriptionTransport:
    """
    Resolve the transport to use for making GraphQL subscriptions.

    :param endpoint: The GraphQL endpoint URL.
    :param transport: The transport to use. If not provided, the best available
        transport is automatically selected. Must be a
        :class:`GraphQLSubscriptionTransport` instance.
    :param session: An optional `GraphQLSession`.
    :param kwargs: Additional arguments to pass to the transport constructor.
    :return: A GraphQLSubscriptionTransport instance.
    :raises ImportError: If the requested transport is not available.
    :raises RuntimeError: If "auto" transport is requested but no suitable transport is
        available.
    """
    if transport is not None:
        return transport

    # auto or None
    if _is_aiohttp_available():
        from aiographql.client.transport.aiohttp import AiohttpSubscriptionTransport

        return AiohttpSubscriptionTransport(
            endpoint=endpoint,
            session=cast("aiohttp.ClientSession | None", session),
            **kwargs,
        )

    if _is_websockets_available():
        from aiographql.client.transport.websocket import WebsocketSubscriptionTransport

        return WebsocketSubscriptionTransport(endpoint=endpoint, **kwargs)

    raise RuntimeError(
        "No suitable subscription transport found. Please install `aiohttp` or `websockets` via extras, "
        "e.g., `pip install aiographql-client[aiohttp]` or `pip install aiographql-client[websockets]`."
    )
