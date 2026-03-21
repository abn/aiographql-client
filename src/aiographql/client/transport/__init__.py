from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Any

from aiographql.client.transport.base import GraphQLTransport
from aiographql.client.transport.resolver import get_default_transport


if TYPE_CHECKING:
    from aiographql.client.transport.http import AiohttpTransport
    from aiographql.client.transport.http import HttpxTransport


def __getattr__(name: str) -> Any:
    if name == "AiohttpTransport":
        from aiographql.client.transport.http import AiohttpTransport

        return AiohttpTransport
    if name == "HttpxTransport":
        from aiographql.client.transport.http import HttpxTransport

        return HttpxTransport
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "AiohttpTransport",
    "GraphQLTransport",
    "HttpxTransport",
    "get_default_transport",
]
