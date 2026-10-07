from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Any

from aiographql.client.client import GraphQLClient
from aiographql.client.client import GraphQLQueryMethod
from aiographql.client.codec import DefaultGraphQLCodec
from aiographql.client.codec import GraphQLCodec
from aiographql.client.error import GraphQLError
from aiographql.client.exceptions import GraphQLClientException
from aiographql.client.exceptions import GraphQLClientValidationException
from aiographql.client.exceptions import GraphQLCodecException
from aiographql.client.exceptions import GraphQLIntrospectionException
from aiographql.client.exceptions import GraphQLRequestException
from aiographql.client.request import GraphQLRequest
from aiographql.client.response import GraphQLResponse
from aiographql.client.subscription import GRAPHQL_TRANSPORT_WS_PROTOCOL
from aiographql.client.subscription import GRAPHQL_WS_PROTOCOL
from aiographql.client.subscription import GraphQLSubscription
from aiographql.client.subscription import GraphQLSubscriptionEvent
from aiographql.client.subscription import GraphQLSubscriptionEventType
from aiographql.client.transport import GraphQLTransport


if TYPE_CHECKING:
    from aiographql.client.transport import AiohttpTransport
    from aiographql.client.transport import HttpxTransport


def __getattr__(name: str) -> Any:
    if name == "AiohttpTransport":
        from aiographql.client.transport import AiohttpTransport

        return AiohttpTransport
    if name == "HttpxTransport":
        from aiographql.client.transport import HttpxTransport

        return HttpxTransport
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "GRAPHQL_TRANSPORT_WS_PROTOCOL",
    "GRAPHQL_WS_PROTOCOL",
    "AiohttpTransport",
    "DefaultGraphQLCodec",
    "GraphQLClient",
    "GraphQLClientException",
    "GraphQLClientValidationException",
    "GraphQLCodec",
    "GraphQLCodecException",
    "GraphQLError",
    "GraphQLIntrospectionException",
    "GraphQLQueryMethod",
    "GraphQLRequest",
    "GraphQLRequestException",
    "GraphQLResponse",
    "GraphQLSubscription",
    "GraphQLSubscriptionEvent",
    "GraphQLSubscriptionEventType",
    "GraphQLTransport",
    "HttpxTransport",
]
