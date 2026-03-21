from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Any

from aiographql.client.transport.base import GraphQLSession
from aiographql.client.transport.base import GraphQLSubscriptionTransport
from aiographql.client.transport.base import GraphQLTransport
from aiographql.client.transport.resolver import get_default_subscription_transport
from aiographql.client.transport.resolver import get_default_transport


if TYPE_CHECKING:
    from aiographql.client.transport.http import AiohttpSubscriptionTransport
    from aiographql.client.transport.http import AiohttpTransport
    from aiographql.client.transport.http import HttpxTransport


def __getattr__(name: str) -> Any:
    if name == "AiohttpTransport":
        from aiographql.client.transport.http import AiohttpTransport

        return AiohttpTransport
    if name == "HttpxTransport":
        from aiographql.client.transport.http import HttpxTransport

        return HttpxTransport
    if name == "AiohttpSubscriptionTransport":
        from aiographql.client.transport.http import AiohttpSubscriptionTransport

        return AiohttpSubscriptionTransport
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "AiohttpSubscriptionTransport",
    "AiohttpTransport",
    "GraphQLSession",
    "GraphQLSubscriptionTransport",
    "GraphQLTransport",
    "HttpxTransport",
    "get_default_subscription_transport",
    "get_default_transport",
]
