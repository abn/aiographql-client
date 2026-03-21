from __future__ import annotations

import importlib.metadata

from typing import TYPE_CHECKING
from typing import Any
from typing import Literal


if TYPE_CHECKING:
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


def get_default_transport(
    endpoint: str,
    transport: Literal["auto", "httpx", "aiohttp"] | GraphQLTransport | None = "auto",
    **kwargs: Any,
) -> GraphQLTransport:
    """
    Resolve the transport to use for making GraphQL requests.

    :param endpoint: The GraphQL endpoint URL.
    :param transport: The transport to use. Can be "auto", "httpx", "aiohttp", or a
        GraphQLTransport instance. Defaults to "auto".
    :param kwargs: Additional arguments to pass to the transport constructor.
    :return: A GraphQLTransport instance.
    :raises ImportError: If the requested transport is not available.
    :raises RuntimeError: If "auto" transport is requested but no suitable transport is
        available.
    """
    if not isinstance(transport, str) and transport is not None:
        return transport

    if transport == "httpx":
        from aiographql.client.transport.http import HttpxTransport

        if not _is_httpx_available(min_version="0.0.0"):  # Any version if explicit
            raise ImportError(
                "httpx is not installed. Install it with `pip install aiographql-client[httpx]`."
            )
        return HttpxTransport(endpoint=endpoint, **kwargs)

    if transport == "aiohttp":
        from aiographql.client.transport.http import AiohttpTransport

        if not _is_aiohttp_available():
            raise ImportError(
                "aiohttp is not installed. Install it with `pip install aiographql-client[aiohttp]`."
            )
        return AiohttpTransport(endpoint=endpoint, **kwargs)

    # auto or None
    if _is_aiohttp_available():
        from aiographql.client.transport.http import AiohttpTransport

        return AiohttpTransport(endpoint=endpoint, **kwargs)

    if _is_httpx_available():
        from aiographql.client.transport.http import HttpxTransport

        return HttpxTransport(endpoint=endpoint, **kwargs)

    raise RuntimeError(
        "No suitable transport found. Please install either `aiohttp` or `httpx>=0.24.0` via extras, "
        "e.g., `pip install aiographql-client[aiohttp]` or `pip install aiographql-client[httpx]`."
    )
