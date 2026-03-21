from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Any
from typing import Protocol
from typing import runtime_checkable

from aiographql.client.exceptions import GraphQLClientException
from aiographql.client.exceptions import GraphQLRequestException
from aiographql.client.helpers import aiohttp_client_session
from aiographql.client.response import GraphQLResponse


if TYPE_CHECKING:
    import aiohttp

    from aiographql.client.request import GraphQLRequest
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
        session: aiohttp.ClientSession | None = None,
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


class AiohttpTransport(GraphQLTransport):
    """
    Aiohttp implementation of GraphQLTransport.
    """

    def __init__(
        self,
        endpoint: str,
        session: aiohttp.ClientSession | None = None,
    ) -> None:
        self.endpoint = endpoint
        self._session = session

    async def request(
        self,
        method: str,
        request: GraphQLRequest,
        serializer: GraphQLSerializer,
        session: aiohttp.ClientSession | None = None,
        **kwargs: Any,
    ) -> GraphQLResponse:
        """
        Execute a GraphQL request using aiohttp.
        """
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

        # use provided session, or internal session, or create a temporary one
        actual_session = session or self._session
        if actual_session:
            return await self._http_request(
                actual_session, method, request, serializer, **kwargs
            )

        async with aiohttp_client_session() as temp_session:
            return await self._http_request(
                temp_session, method, request, serializer, **kwargs
            )

    async def _http_request(
        self,
        session: aiohttp.ClientSession,
        method: str,
        request: GraphQLRequest,
        serializer: GraphQLSerializer,
        **kwargs: Any,
    ) -> GraphQLResponse:
        async with session.request(
            method=method, url=self.endpoint, headers=request.headers, **kwargs
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

    def _coerce_value(self, value: Any, serializer: GraphQLSerializer) -> Any:
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
        if self._session is not None:
            await self._session.close()
