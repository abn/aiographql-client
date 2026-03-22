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

        # websockets.connect expects ws:// or wss://
        if endpoint.startswith("http://"):
            endpoint = f"ws://{endpoint[7:]}"
        elif endpoint.startswith("https://"):
            endpoint = f"wss://{endpoint[8:]}"

        # websockets.connect expects headers as a dict or list
        if request.headers:
            # websockets 14.0+ uses additional_headers in asyncio.connect
            # earlier versions and legacy use extra_headers.
            # We try to use additional_headers if it's available in the signature.
            # We use the version check as a fallback or primary method if inspect fails.
            import importlib.metadata

            import websockets

            try:
                version = importlib.metadata.version("websockets")
                major_version = int(version.split(".")[0])
                is_websockets_14_plus = major_version >= 14
            except (importlib.metadata.PackageNotFoundError, ValueError):
                is_websockets_14_plus = False

            if is_websockets_14_plus:
                kwargs.setdefault("additional_headers", request.headers)
            else:
                kwargs.setdefault("extra_headers", request.headers)

        # Remove unsupported kwargs
        kwargs.pop("session", None)
        subprotocols = kwargs.pop("protocols", None)
        if subprotocols:
            kwargs.setdefault("subprotocols", subprotocols)

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
