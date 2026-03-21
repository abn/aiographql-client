from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Any
from typing import Protocol
from typing import runtime_checkable


if TYPE_CHECKING:
    from aiographql.client.request import GraphQLRequest
    from aiographql.client.response import GraphQLResponse
    from aiographql.client.serializer import GraphQLSerializer


@runtime_checkable
class GraphQLTransport(Protocol):
    """
    Protocol for GraphQL transports.
    """

    async def request(
        self,
        method: str,
        request: GraphQLRequest,
        serializer: GraphQLSerializer,
        **kwargs: Any,
    ) -> GraphQLResponse:
        """
        Execute a GraphQL request.
        """
        ...

    async def close(self) -> None:
        """
        Close the transport and any underlying resources.
        """
        ...


@runtime_checkable
class GraphQLSubscriptionTransport(Protocol):
    """
    Protocol for GraphQL subscription transports.
    """

    async def subscribe(
        self,
        endpoint: str,
        request: GraphQLRequest,
        serializer: GraphQLSerializer,
        **kwargs: Any,
    ) -> Any:
        """
        Execute a GraphQL subscription.
        """
        ...

    async def close(self) -> None:
        """
        Close the transport and any underlying resources.
        """
        ...
