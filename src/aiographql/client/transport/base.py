from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Any
from typing import Protocol
from typing import TypeAlias
from typing import Union
from typing import runtime_checkable


if TYPE_CHECKING:
    import aiohttp
    import httpx

    from aiographql.client.request import GraphQLRequest
    from aiographql.client.response import GraphQLResponse
    from aiographql.client.serializer import GraphQLSerializer


GraphQLSession: TypeAlias = Union["aiohttp.ClientSession", "httpx.AsyncClient"]

GRAPHQL_RESPONSE_MEDIA_TYPE: str = "application/graphql-response+json"


def prepare_get_params(
    request: GraphQLRequest, serializer: GraphQLSerializer
) -> dict[str, str]:
    """
    Prepare GET query parameters conforming to the GraphQL-over-HTTP specification.
    """
    params: dict[str, str] = {"query": request.query}
    if request.operationName is not None:
        params["operationName"] = request.operationName
    if request.variables:
        encoded_vars = request.payload().get("variables")
        if encoded_vars:
            serialized = serializer.dumps(encoded_vars)
            params["variables"] = (
                serialized.decode("utf-8")
                if isinstance(serialized, bytes)
                else str(serialized)
            )
    if request.extensions:
        serialized = serializer.dumps(request.extensions)
        params["extensions"] = (
            serialized.decode("utf-8")
            if isinstance(serialized, bytes)
            else str(serialized)
        )
    return params


def _is_valid_graphql_payload(body: Any) -> bool:
    if not isinstance(body, dict):
        return False
    has_data = "data" in body
    has_errors = "errors" in body
    if not (has_data or has_errors):
        return False
    if has_errors:
        errors = body["errors"]
        if not isinstance(errors, list) or not all(
            isinstance(err, dict) for err in errors
        ):
            return False
    if has_data:
        data = body["data"]
        if data is not None and not isinstance(data, dict):
            return False
    return True


def is_graphql_response(status_code: int, content_type: str | None, body: Any) -> bool:
    """
    Determine if an HTTP response represents a valid GraphQL execution response
    under the GraphQL-over-HTTP specification.
    """
    if 200 <= status_code < 300:
        return True
    if content_type:
        media_type = content_type.split(";")[0].strip().lower()
        if media_type == GRAPHQL_RESPONSE_MEDIA_TYPE and _is_valid_graphql_payload(
            body
        ):
            return True
    return False


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
class GraphQLWebSocketResponse(Protocol):
    """
    Protocol for GraphQL WebSocket responses.
    """

    async def __aenter__(self) -> GraphQLWebSocketResponse: ...

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None: ...

    async def send_str(self, data: str) -> None: ...

    def __aiter__(self) -> GraphQLWebSocketResponse: ...

    async def __anext__(self) -> Any: ...


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
    ) -> GraphQLWebSocketResponse:
        """
        Execute a GraphQL subscription.
        """
        ...

    async def close(self) -> None:
        """
        Close the transport and any underlying resources.
        """
        ...
