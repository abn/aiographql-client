from __future__ import annotations

import importlib

from typing import TYPE_CHECKING
from typing import Any

from aiographql.client.exceptions import GraphQLClientException
from aiographql.client.exceptions import GraphQLRequestException
from aiographql.client.exceptions import GraphQLTransportException
from aiographql.client.response import GraphQLResponse
from aiographql.client.transport.base import GraphQLSubscriptionTransport
from aiographql.client.transport.base import GraphQLTransport
from aiographql.client.transport.base import GraphQLWebSocketResponse


if TYPE_CHECKING:
    import aiohttp

    from aiographql.client.request import GraphQLRequest
    from aiographql.client.serializer import GraphQLSerializer


class AiohttpTransport(GraphQLTransport):
    """
    Aiohttp implementation of GraphQLTransport.
    """

    def __init__(
        self,
        endpoint: str,
        session: aiohttp.ClientSession | None = None,
    ) -> None:
        try:
            importlib.import_module("aiohttp")
        except ImportError:
            raise GraphQLClientException(
                "aiohttp is required to use AiohttpTransport. "
                "Install it with `pip install aiographql-client[aiohttp]`."
            ) from None

        self.endpoint = endpoint
        self._session = session
        self._owns_session = False

    @staticmethod
    async def create_default_connector() -> aiohttp.TCPConnector:
        import sys

        import aiohttp

        connector_kwargs: dict[str, Any] = {"force_close": True, "limit": 100}
        if sys.version_info < (3, 12, 13):
            connector_kwargs["enable_cleanup_closed"] = True

        return aiohttp.TCPConnector(**connector_kwargs)

    async def _get_session(self) -> aiohttp.ClientSession:
        """
        Get or create the internal aiohttp session.
        """
        import aiohttp

        if self._session is None:
            self._session = aiohttp.ClientSession(
                connector=await self.create_default_connector()
            )
            self._owns_session = True

        return self._session

    async def request(
        self,
        method: str,
        request: GraphQLRequest,
        serializer: GraphQLSerializer,
        **kwargs: Any,
    ) -> GraphQLResponse:
        """
        Execute a GraphQL request using aiohttp.
        """
        # Remove 'client' from kwargs if it exists, as aiohttp doesn't support it
        kwargs.pop("client", None)

        method = method.lower()
        if method == "post":
            kwargs.setdefault("data", serializer.dumps(request.payload()))
        elif method == "get":
            params = {
                k: str(v)
                if not isinstance(v, (dict, list, bool))
                else self._coerce_value(v, serializer)
                for k, v in request.payload().items()
            }
            kwargs.setdefault("params", params)
        else:
            raise GraphQLClientException(f"Invalid method ({method}) specified")

        # use provided session, or internal session
        actual_session = kwargs.pop("session", None) or await self._get_session()
        return await self._http_request(
            actual_session, method, request, serializer, **kwargs
        )

    async def _http_request(
        self,
        session: aiohttp.ClientSession,
        method: str,
        request: GraphQLRequest,
        serializer: GraphQLSerializer,
        **kwargs: Any,
    ) -> GraphQLResponse:
        import aiohttp

        try:
            async with session.request(
                method=method,
                url=self.endpoint,
                headers=request.headers,
                **kwargs,
            ) as resp:
                resp_data = await resp.read()
                try:
                    body = serializer.loads(resp_data)
                except Exception:
                    body = None

                response = GraphQLResponse(request=request, json=body)

                if 200 <= resp.status < 300:
                    return response

                raise GraphQLRequestException(response)
        except aiohttp.ClientError as exc:
            raise GraphQLTransportException(f"HTTP request failed: {exc}") from exc

    @staticmethod
    def _coerce_value(value: Any, serializer: GraphQLSerializer) -> Any:
        if isinstance(value, bool):
            return int(value)
        if isinstance(value, (dict, list)):
            serialized = serializer.dumps(value)
            return (
                serialized.decode("utf-8")
                if isinstance(serialized, bytes)
                else serialized
            )
        return value

    async def close(self) -> None:
        if self._session is not None and self._owns_session:
            await self._session.close()
            self._session = None
            self._owns_session = False


class AiohttpSubscriptionTransport(GraphQLSubscriptionTransport):
    """
    Aiohttp implementation of GraphQLSubscriptionTransport.
    """

    def __init__(
        self,
        endpoint: str,
        session: aiohttp.ClientSession | None = None,
    ) -> None:
        try:
            importlib.import_module("aiohttp")
        except ImportError:
            raise GraphQLClientException(
                "aiohttp is required to use AiohttpSubscriptionTransport. "
                "Install it with `pip install aiographql-client[aiohttp]`."
            ) from None

        self.endpoint = endpoint
        self._session = session
        self._owns_session = False

    async def _get_session(self) -> aiohttp.ClientSession:
        """
        Get or create the internal aiohttp session.
        """
        import aiohttp

        if self._session is None:
            self._session = aiohttp.ClientSession(
                connector=await AiohttpTransport.create_default_connector()
            )
            self._owns_session = True

        return self._session

    async def subscribe(
        self,
        endpoint: str,
        request: GraphQLRequest,
        serializer: GraphQLSerializer,
        **kwargs: Any,
    ) -> GraphQLWebSocketResponse:
        """
        Execute a GraphQL subscription using aiohttp websockets.
        """
        # ws_connect expects ws:// or wss://
        if endpoint.startswith("http://"):
            endpoint = f"ws://{endpoint[7:]}"
        elif endpoint.startswith("https://"):
            endpoint = f"wss://{endpoint[8:]}"

        # use provided session, or internal session
        actual_session = kwargs.pop("session", None) or await self._get_session()

        # pass headers from request to the websocket upgrade
        if request.headers:
            kwargs.setdefault("headers", request.headers)

        return AiohttpWebSocketResponse(
            await actual_session.ws_connect(endpoint, **kwargs)
        )

    async def close(self) -> None:
        if self._session is not None and self._owns_session:
            await self._session.close()
            self._session = None
            self._owns_session = False


class AiohttpWebSocketResponse(GraphQLWebSocketResponse):
    def __init__(self, ws: aiohttp.ClientWebSocketResponse) -> None:
        self.ws = ws

    @property
    def subprotocol(self) -> str | None:
        return self.ws.protocol

    async def __aenter__(self) -> AiohttpWebSocketResponse:
        # aiohttp.ClientWebSocketResponse does not have __aenter__, so return self
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        # ClientWebSocketResponse has a close() method.
        await self.ws.close()

    async def send_str(self, data: str) -> None:
        import asyncio

        res = self.ws.send_str(data)
        if asyncio.iscoroutine(res):
            await res

    def __aiter__(self) -> AiohttpWebSocketResponse:
        return self

    async def __anext__(self) -> Any:
        import aiohttp

        while True:
            msg = await self.ws.receive()

            # aiohttp-style message object
            if hasattr(msg, "type"):
                if msg.type == aiohttp.WSMsgType.TEXT:
                    return msg.data

                if msg.type in (
                    aiohttp.WSMsgType.CLOSE,
                    aiohttp.WSMsgType.CLOSED,
                    aiohttp.WSMsgType.CLOSING,
                    aiohttp.WSMsgType.ERROR,
                ):
                    raise StopAsyncIteration

                continue

            # transport returned plain data
            return msg
