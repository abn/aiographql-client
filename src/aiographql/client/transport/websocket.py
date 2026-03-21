from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Any

from aiographql.client.transport.base import GraphQLSubscriptionTransport
from aiographql.client.transport.base import GraphQLWebSocketResponse


if TYPE_CHECKING:
    from websockets.asyncio.client import ClientConnection

    from aiographql.client.request import GraphQLRequest
    from aiographql.client.serializer import GraphQLSerializer


class WebsocketSubscriptionTransport(GraphQLSubscriptionTransport):
    """
    Websockets implementation of GraphQLSubscriptionTransport.
    """

    def __init__(self, endpoint: str) -> None:
        self.endpoint = endpoint

    async def subscribe(
        self,
        endpoint: str,
        request: GraphQLRequest,
        serializer: GraphQLSerializer,
        **kwargs: Any,
    ) -> GraphQLWebSocketResponse:
        """
        Execute a GraphQL subscription using websockets.
        """
        import websockets

        # websockets.connect expects headers as a dict or list
        if request.headers:
            kwargs.setdefault("extra_headers", request.headers)

        # Remove unsupported kwargs
        kwargs.pop("session", None)
        kwargs.pop("protocols", None)

        return WebsocketResponse(await websockets.connect(endpoint, **kwargs))

    async def close(self) -> None:
        pass


class WebsocketResponse(GraphQLWebSocketResponse):
    def __init__(self, ws: ClientConnection) -> None:
        self.ws = ws

    async def __aenter__(self) -> WebsocketResponse:
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        await self.ws.close()

    async def send_str(self, data: str) -> None:
        await self.ws.send(data)

    def __aiter__(self) -> WebsocketResponse:
        return self

    async def __anext__(self) -> Any:
        import websockets.exceptions

        try:
            return await self.ws.recv()
        except websockets.exceptions.ConnectionClosed:
            raise StopAsyncIteration
