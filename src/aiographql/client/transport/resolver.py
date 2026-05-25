from __future__ import annotations

import importlib
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


def _is_module_available(module_name: str, min_version: str | None = None) -> bool:
    """
    Check if a module is available and optionally meets a minimum version requirement.
    """
    try:
        importlib.import_module(module_name)
        if min_version is None:
            return True

        version = importlib.metadata.version(module_name)
        parts = [int(p) for p in version.split(".") if p.isdigit()]
        min_parts = [int(p) for p in min_version.split(".") if p.isdigit()]
        return parts >= min_parts
    except (ImportError, importlib.metadata.PackageNotFoundError, ValueError):
        return False


def _is_httpx_available(min_version: str = "0.24.0") -> bool:
    return _is_module_available("httpx", min_version=min_version)


def _is_aiohttp_available() -> bool:
    return _is_module_available("aiohttp")


def _is_websockets_available() -> bool:
    return _is_module_available("websockets")


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

    if _is_module_available("aiohttp"):
        from aiographql.client.transport.aiohttp import AiohttpTransport

        return AiohttpTransport(
            endpoint=endpoint,
            session=cast("aiohttp.ClientSession | None", session),
            **kwargs,
        )

    if _is_module_available("httpx", min_version="0.24.0"):
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
    if _is_module_available("aiohttp"):
        from aiographql.client.transport.aiohttp import AiohttpSubscriptionTransport

        return AiohttpSubscriptionTransport(
            endpoint=endpoint,
            session=cast("aiohttp.ClientSession | None", session),
            **kwargs,
        )

    if _is_module_available("websockets"):
        from aiographql.client.transport.websocket import WebsocketSubscriptionTransport

        return WebsocketSubscriptionTransport(endpoint=endpoint, **kwargs)

    raise RuntimeError(
        "No suitable subscription transport found. Please install `aiohttp` or `websockets` via extras, "
        "e.g., `pip install aiographql-client[aiohttp]` or `pip install aiographql-client[httpx]`."
    )
