from __future__ import annotations

import importlib

from typing import TYPE_CHECKING
from typing import Any

from aiographql.client.exceptions import GraphQLClientException
from aiographql.client.exceptions import GraphQLRequestException
from aiographql.client.exceptions import GraphQLTransportException
from aiographql.client.response import GraphQLResponse
from aiographql.client.transport.base import GraphQLTransport
from aiographql.client.transport.base import is_graphql_response
from aiographql.client.transport.base import prepare_get_params


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
            importlib.import_module("httpx")
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
        # use provided client, or internal client, or create a temporary one
        actual_client = (
            kwargs.pop("client", None)
            or kwargs.pop("session", None)
            or await self._get_client()
        )

        method = method.upper()
        if method == "POST":
            kwargs.setdefault("content", serializer.dumps(request.payload()))
        elif method == "GET":
            kwargs.setdefault("params", prepare_get_params(request, serializer))
        else:
            raise GraphQLClientException(f"Invalid method ({method}) specified")

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
            resp_data = getattr(resp, "content", None)
            if resp_data is None:
                try:
                    # In some environments/mocking scenarios, resp.read() might be sync or async
                    import asyncio

                    read_coro = resp.read()
                    if asyncio.iscoroutine(read_coro):
                        resp_data = await read_coro
                    else:
                        resp_data = read_coro
                except (AttributeError, TypeError):
                    resp_data = None

            try:
                body = serializer.loads(resp_data) if resp_data is not None else None
            except Exception:
                body = None

            response = GraphQLResponse(
                request=request, json=body if isinstance(body, dict) else {}
            )

            status_code = int(getattr(resp, "status_code", getattr(resp, "status", 0)))
            content_type = getattr(resp, "headers", {}).get("content-type")
            if is_graphql_response(status_code, content_type, body):
                return response

            raise GraphQLRequestException(response)
        except Exception as exc:
            import httpx

            if isinstance(exc, httpx.HTTPError):
                if isinstance(exc, httpx.HTTPStatusError):
                    # This should have been handled by the status_code check above if
                    # raise_for_status() was called, but we do it manually.
                    # If we get here, it might be an exception from httpx internals
                    # or if the user passed an unexpected exception.
                    pass
                raise GraphQLTransportException(f"HTTP request failed: {exc}") from exc
            raise

    async def close(self) -> None:
        if self._client is not None and self._owns_client:
            await self._client.aclose()
            self._client = None
            self._owns_client = False
