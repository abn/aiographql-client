from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Any

from aiographql.client.exceptions import GraphQLClientException
from aiographql.client.exceptions import GraphQLRequestException
from aiographql.client.response import GraphQLResponse
from aiographql.client.transport.base import GraphQLTransport


if TYPE_CHECKING:
    import httpx

    from aiographql.client.request import GraphQLRequest
    from aiographql.client.serializer import GraphQLSerializer


class HttpxTransport(GraphQLTransport):
    """
    Httpx implementation of GraphQLTransport.
    """

    def __init__(
        self,
        endpoint: str,
        client: httpx.AsyncClient | None = None,
        session: httpx.AsyncClient | None = None,
    ) -> None:
        try:
            import httpx as _  # noqa: F401
        except ImportError:
            raise GraphQLClientException(
                "httpx is required to use HttpxTransport. "
                "Install it with `pip install aiographql-client[httpx]`."
            ) from None

        self.endpoint = endpoint
        self._client = client or session
        self._owns_client = False

    async def _get_client(self) -> httpx.AsyncClient:
        """
        Get or create the internal httpx client.
        """
        import httpx

        if self._client is None:
            self._client = httpx.AsyncClient()
            self._owns_client = True

        return self._client

    async def request(
        self,
        method: str,
        request: GraphQLRequest,
        serializer: GraphQLSerializer,
        **kwargs: Any,
    ) -> GraphQLResponse:
        """
        Execute a GraphQL request using httpx.
        """
        # Remove 'session' from kwargs if it exists, as httpx doesn't support it
        # and we already handled it in __init__
        kwargs.pop("session", None)

        method = method.upper()
        if method == "POST":
            kwargs.setdefault("content", serializer.dumps(request.payload()))
        elif method == "GET":
            params = {
                k: str(v)
                if not isinstance(v, (dict, list, bool))
                else self._coerce_value(v, serializer)
                for k, v in request.payload().items()
            }
            kwargs.setdefault("params", params)
        else:
            raise GraphQLClientException(f"Invalid method ({method}) specified")

        # use provided client, or internal client, or create a temporary one
        actual_client = kwargs.pop("client", None) or await self._get_client()
        return await self._http_request(
            actual_client, method, request, serializer, **kwargs
        )

    async def _http_request(
        self,
        client: httpx.AsyncClient,
        method: str,
        request: GraphQLRequest,
        serializer: GraphQLSerializer,
        **kwargs: Any,
    ) -> GraphQLResponse:
        import httpx

        try:
            resp = await client.request(
                method=method,
                url=self.endpoint,
                headers=request.headers,
                **kwargs,
            )
            resp_data = resp.content
            try:
                body = serializer.loads(resp_data)
            except Exception:
                body = None

            response = GraphQLResponse(request=request, json=body)

            if 200 <= resp.status_code < 300:
                return response

            raise GraphQLRequestException(response)
        except httpx.HTTPError as exc:
            if isinstance(exc, httpx.HTTPStatusError):
                # This should have been handled by the status_code check above if
                # raise_for_status() was called, but we do it manually.
                # If we get here, it might be an exception from httpx internals
                # or if the user passed an unexpected exception.
                pass
            raise GraphQLClientException(f"HTTP request failed: {exc}") from exc

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
        if self._client is not None and self._owns_client:
            await self._client.aclose()
            self._client = None
            self._owns_client = False
