from __future__ import annotations

import asyncio
import dataclasses

from typing import TYPE_CHECKING
from typing import Any
from typing import Literal
from typing import cast

import graphql

from cafeteria.asyncio.callbacks import CallbackRegistry
from cafeteria.asyncio.callbacks import CallbackType

from aiographql.client.exceptions import GraphQLClientValidationException
from aiographql.client.exceptions import GraphQLIntrospectionException
from aiographql.client.request import GraphQLRequest
from aiographql.client.serializer import DefaultSerializer
from aiographql.client.serializer import GraphQLSerializer
from aiographql.client.subscription import CallbacksType
from aiographql.client.subscription import GraphQLSubscription
from aiographql.client.subscription import GraphQLSubscriptionEventType
from aiographql.client.transport import GraphQLSubscriptionTransport
from aiographql.client.transport import GraphQLTransport
from aiographql.client.transport import get_default_subscription_transport
from aiographql.client.transport import get_default_transport


if TYPE_CHECKING:
    from collections.abc import Iterable
    from collections.abc import Mapping

    from aiographql.client.codec import GraphQLCodec
    from aiographql.client.codec import T
    from aiographql.client.response import GraphQLResponse
    from aiographql.client.transport import GraphQLSession
    from aiographql.client.transport import GraphQLTransport


@dataclasses.dataclass(frozen=True)
class GraphQLQueryMethod:
    post: str = "post"
    get: str = "get"


class GraphQLClient:
    """
    Client implementation handling all interactions with a specified endpoint. The
    following example shows how to make a simple query.

    .. code-block:: python

        client = GraphQLClient(
            endpoint="http://127.0.0.1:8080/v1/graphql",
            headers={"Authorization": "Bearer <token>"},
        )
        response: GraphQLResponse = await client.query("{ city { name } }")

    You can also use an application scoped :class:`aiohttp.ClientSession` throughout
    the life of the client as show below.

    .. code-block:: python
        :emphasize-lines: 1,4

        async with aiohttp.ClientSession() as session:
            client = GraphQLClient(
                endpoint="http://127.0.0.1:8080/v1/graphql",
                session=session
            )

    :param endpoint: URI of graph api.
    :param headers: Default headers to use for every request made by this client.
        By default the client adds 'Content-Type: application/json' and
        'Accept-Encoding: gzip' to all requests. These can be overridden by
        specifying then here.
    :param method: Default method to use when submitting a GraphQL request to the
        specified `endpoint`.
    :param session: Optional `aiohttp.ClientSession` to use when making requests.
        This is expected to be externally managed.
    :param validate: If set to `False`, the client will not attempt to validate
        requests against the schema from the server. This is useful when
        introspection is disabled on the server.
    :param serializer: Custom JSON serializer to use for requests and responses.
    :param codec: Custom codec to use for encoding request variables and decoding
        response data.
    :param transport: Custom transport to use for making requests. If not provided,
        the best available transport is automatically selected (preferring httpx).
        Can be "auto", "httpx", "aiohttp" or a :class:`GraphQLTransport` instance.
    """

    def __init__(
        self,
        endpoint: str,
        headers: Mapping[str, str] | None = None,
        method: str | None = None,
        schema: graphql.GraphQLSchema | None = None,
        session: GraphQLSession | None = None,
        validate: bool = True,
        serializer: GraphQLSerializer | None = None,
        codec: GraphQLCodec | None = None,
        transport: Literal["auto", "httpx", "aiohttp"] | GraphQLTransport | None = None,
    ) -> None:
        self.endpoint = endpoint
        self._method = method or GraphQLQueryMethod.post
        self._headers = {"Content-Type": "application/json", "Accept-Encoding": "gzip"}
        self._headers.update(headers or {})
        self._schema = schema
        self._validate = validate
        self._serializer = serializer or DefaultSerializer()
        self._codec = codec
        self._transport = get_default_transport(
            endpoint=self.endpoint,
            transport=transport,
            session=session,
        )

    @property
    def transport(self) -> GraphQLTransport:
        return self._transport

    def _session(self) -> GraphQLSession | None:
        if hasattr(self._transport, "_session"):
            return cast("GraphQLSession | None", self._transport._session)
        if hasattr(self._transport, "_client"):
            return cast("GraphQLSession | None", self._transport._client)
        return None

    def _aiohttp_session(self) -> Any | None:
        try:
            import aiohttp

            _session = self._session()
            if isinstance(_session, aiohttp.ClientSession):
                return _session
        except ImportError:
            pass
        return None

    async def close(self) -> None:
        """
        Close the underlying transport.
        """
        await self._transport.close()

    async def __aenter__(self) -> GraphQLClient:
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        await self.close()

    async def introspect(
        self, headers: dict[str, str] | None = None
    ) -> graphql.GraphQLSchema:
        """
        Introspect the GraphQL endpoint specified for this client and return a
        `graphql.GraphQLSchema` object specifying the schema associated with this
        endpoint.

        :return: GraphQL schema for the configured endpoint
        """
        request = GraphQLRequest(
            query=graphql.get_introspection_query(descriptions=False),
            validate=False,
            headers=headers or {},
        )
        introspection = await self.query(request)
        try:
            return graphql.build_client_schema(
                cast("graphql.IntrospectionQuery", introspection.data)
            )
        except TypeError:
            raise GraphQLIntrospectionException(
                f"Failed to build schema from introspection data: {introspection.errors}"
            ) from None

    async def get_schema(
        self, refresh: bool = False, headers: dict[str, str] | None = None
    ) -> graphql.GraphQLSchema:
        """
        Get the introspected schema for the endpoint used by this client. If an
        unexpired cache exists, this is returned unless the `refresh` parameter is set
        to True.

        :param refresh: Refresh the cached schema by forcing an introspection of the
            GraphQL endpoint.
        :param headers: Request headers
        :return: The GraphQL schema as introspected. This maybe a previously cached value.
        """
        # TODO: consider adding ttl logic for expiring schemas for long running services
        if self._schema is None or refresh:
            self._schema = await self.introspect(headers=headers)
        return self._schema

    async def validate(
        self,
        request: GraphQLRequest,
        schema: graphql.GraphQLSchema | None = None,
        headers: dict[str, str] | None = None,
        force: bool = False,
    ) -> None:
        """
        Validate a given request against a schema (provided or fetched). Validation is
        skipped if the request's `validate` property is set to `False` unless forced.

        :param request: Request that is to be validated.
        :param schema: Schema against which provided request should be validated, if
                       different from `GraphQLRequest.schema` or as fetched from the
                       client endpoint.
        :param headers: Headers to be set when fetching the schema from the client
                        endpoint. If provided, request headers are ignored.
        :param force: Force validation even if the provided request has validation
                      disabled.
        """
        if not force and (not self._validate or not request.validate):
            # skip validation if client or request validate flag is set to false
            return

        schema = schema or await self.get_schema(headers=headers or request.headers)
        errors = await asyncio.get_running_loop().run_in_executor(
            None, graphql.validate, schema, graphql.parse(request.query)
        )
        if errors:
            raise GraphQLClientValidationException(*errors)

    def _prepare_request(
        self,
        request: GraphQLRequest | str,
        operation: str | None = None,
        variables: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> GraphQLRequest:
        """
        Helper method to ensure that queries handle both string and
        :class:`GraphQLRequest` objects.

        :param request: Request to send to the GraphQL server.
        :param operation: GraphQL operation name to use if the `GraphQLRequest.query`
                          contains named operations. This will override any default
                          operation set.
        :param variables: Query variables to set for the provided request. This will
                          override the default values for any existing variables in the
                          request if set.
        :param headers: Additional headers to be set when sending HTTP request.
        :return: A copy of the `request` object with the specified values of
            `operation`, `variables` and `headers` set/merged.
        """
        if isinstance(request, str):
            request = GraphQLRequest(query=request, codec=self._codec)

        request = request.copy(
            headers=headers,
            headers_fallback=self._headers,
            operation=operation,
            variables=variables,
            codec=self._codec,
        )

        if request.codec:
            request = dataclasses.replace(
                request, variables=request.codec.encode(request.variables)
            )

        return request

    async def query_data_as(
        self,
        request: GraphQLRequest | str,
        result_type: type[T],
        path: str | None = None,
        method: str | None = None,
        headers: dict[str, str] | None = None,
        operation: str | None = None,
        variables: dict[str, Any] | None = None,
        session: GraphQLSession | None = None,
    ) -> T:
        """
        Execute a query and decode the response data into a Python object of the
        specified type.

        :param request: Request to send to the GraphQL server.
        :param result_type: The type to decode the data into.
        :param path: An optional dot-separated path to the data to decode.
        :param method: HTTP method to use when submitting request (POST/GET).
        :param headers: Additional headers to be set when sending HTTP request.
        :param operation: GraphQL operation name to use.
        :param variables: Query variables to set for the provided request.
        :param session: Optional `aiohttp.ClientSession` to use for requests.
        :return: The decoded data.
        """
        response = await self.query(
            request=request,
            method=method,
            headers=headers,
            operation=operation,
            variables=variables,
            session=session,
        )
        return response.data_as(result_type, path=path, codec=self._codec)

    async def query(
        self,
        request: GraphQLRequest | str,
        method: str | None = None,
        headers: dict[str, str] | None = None,
        operation: str | None = None,
        variables: dict[str, Any] | None = None,
        session: GraphQLSession | None = None,
    ) -> GraphQLResponse:
        """
        Method to send provided :class:`GraphQLRequest` to the configured endpoint as
        an HTTP request. This method handles the configuration of headers HTTP method
        specific handling of request parameters and/or data as required.

        The order of precedence, least to greatest, of headers is as follows,
            1. client headers (:attr:`GraphQLClient.headers`)
            2. request headers (:attr:`GraphQLRequest.headers`)
            3. `headers` specified as method parameter

        In accordance to the GraphQL specification, any non 2XX response  is treated as
        an error and raises `GraphQLTransactionException` instance.

        :param request: Request to send to the GraphQL server.
        :param method: HTTP method to use when submitting request (POST/GET). If once is
                       not specified, the client default (`GraphQLClient.method`) is
                       used.
        :param headers: Additional headers to be set when sending HTTP request.
        :param operation: GraphQL operation name to use if the `GraphQLRequest.query`
                          contains named operations. This will override any default
                          operation set.
        :param variables: Query variables to set for the provided request. This will
                          override the default values for any existing variables in the
                          request if set.
        :param session: Optional `aiohttp.ClientSession` to use for requests
        :return: The resulting response object.
        """
        request = self._prepare_request(
            request=request, operation=operation, variables=variables, headers=headers
        )

        await self.validate(request=request)
        method = method or self._method

        return await self._transport.request(
            method=method,
            request=request,
            serializer=self._serializer,
            session=session,
        )

    async def post(
        self,
        request: GraphQLRequest,
        headers: dict[str, str] | None = None,
        operation: str | None = None,
        variables: dict[str, Any] | None = None,
        session: GraphQLSession | None = None,
    ) -> GraphQLResponse:
        """
        Helper method that wraps `GraphQLClient.query` with method explicitly set as
        :attr:`GraphQLQueryMethod.post`.

        :param request: Request to send to the GraphQL server.
        :param headers: Additional headers to be set when sending HTTP request.
        :param operation: GraphQL operation name to use if the `GraphQLRequest.query`
                          contains named operations. This will override any default
                          operation set.
        :param variables: Query variables to set for the provided request. This will
                          override the default values for any existing variables in the
                          request if set.
        :param session: Optional `aiohttp.ClientSession` to use for requests
        :return: The resulting `GraphQLResponse` object.
        """
        return await self.query(
            request,
            method=GraphQLQueryMethod.post,
            headers=headers,
            operation=operation,
            variables=variables,
            session=session,
        )

    async def get(
        self,
        request: GraphQLRequest,
        headers: dict[str, str] | None = None,
        operation: str | None = None,
        variables: dict[str, Any] | None = None,
        session: GraphQLSession | None = None,
    ) -> GraphQLResponse:
        """
        Helper method that wraps :method: `GraphQLClient.query` with method explicitly
        set as :attr:`GraphQLQueryMethod.get`.

        :param request: Request to send to the GraphQL server.
        :param headers: Additional headers to be set when sending HTTP request.
        :param operation: GraphQL operation name to use if the `GraphQLRequest.query`
                          contains named operations. This will override any default
                          operation set.
        :param variables: Query variables to set for the provided request. This will
                          override the default values for any existing variables in the
                          request if set.
        :param session: Optional `aiohttp.ClientSession` to use for requests
        :return: The resulting `GraphQLResponse` object.
        """
        return await self.query(
            request,
            method=GraphQLQueryMethod.get,
            headers=headers,
            operation=operation,
            variables=variables,
            session=session,
        )

    async def subscribe(
        self,
        request: GraphQLRequest,
        headers: dict[str, str] | None = None,
        operation: str | None = None,
        variables: dict[str, Any] | None = None,
        callbacks: CallbacksType | None = None,
        on_data: CallbackType | None = None,
        on_error: CallbackType | None = None,
        session: GraphQLSession | None = None,
        wait: bool = False,
        protocols: str | Iterable[str] = (),
        connection_init_payload: dict[str, Any] | None = None,
        transport: Literal["auto", "aiohttp"]
        | GraphQLSubscriptionTransport
        | None = None,
    ) -> GraphQLSubscription:
        """
        Create and initialise a GraphQL subscription. Once subscribed and a known event
        is received, all registered callbacks for the event type is triggered with the
        :class:`aiographql.client.GraphQLSubscriptionEvent` instance passed in the first
        argument.

        The following example will start a subscription that prints all data events as
        it receives them.

        .. code-block:: python

            # initialise and subscribe to events in the background
            subscription: GraphQLSubscription = await client.subscribe(
                request="{ notifications: { id, summary } }",
                on_data=lambda event: print(f"Data: {event}"),
                on_error=lambda event: print(f"Error: {event}"),
            )
            # process events for 10 seconds then unsubscribe
            await asyncio.wait(subscription.task, timeout=10)
            subscription.unsubscribe()

        :param request: Request to send to the GraphQL server.
        :param headers: Additional headers to be set when sending HTTP request.
        :param operation: GraphQL operation name to use if the `GraphQLRequest.query`
                          contains named operations. This will override any default
                          operation set.
        :param variables: Query variables to set for the provided request. This will
                          override the default values for any existing variables in the
                          request if set.
        :param session: Optional `aiohttp.ClientSession` to use for requests
        :return: The resulting `GraphQLResponse` object.
        :param callbacks: Custom callback registry mapping an event to one more more
            callback methods. If not provided, a new instance is created.
        :param on_data: Callback to use when data event is received.
        :param on_error: Callback to use when an error occurs.
        :param session: Optional session to use for connecting the graphql endpoint, if
            one is not provided, a new session is created for the duration of the
            subscription.
        :param wait: If set to `True`, this method will wait until the subscription
            is completed, websocket disconnected or async task cancelled.
        :param protocols: GraphQL over WebSocket Sub-protocol(s) used.
        :param connection_init_payload: Extra fields for the `connection_init` payload.
        :param transport: Custom transport to use for the subscription. If not
            provided, the best available transport is automatically selected.
        :return: The initialised subscription.
        """
        request = self._prepare_request(
            request=request, operation=operation, variables=variables, headers=headers
        )
        await self.validate(request=request)

        callbacks = callbacks or CallbackRegistry()
        if on_data and isinstance(callbacks, CallbackRegistry):
            callbacks.register(GraphQLSubscriptionEventType.DATA, on_data)
        if on_error and isinstance(callbacks, CallbackRegistry):
            callbacks.register(GraphQLSubscriptionEventType.ERROR, on_error)

        subscription = GraphQLSubscription(
            request=request,
            callbacks=callbacks,
            protocols=protocols,
            connection_init_payload=connection_init_payload,
            serializer=self._serializer,
            transport=get_default_subscription_transport(
                endpoint=self.endpoint,
                transport=transport,
                session=session or self._aiohttp_session(),
            ),
        )
        await subscription.subscribe(endpoint=self.endpoint, wait=wait)
        return subscription
