from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, Dict, Mapping, Optional, Union

import aiohttp
import graphql
from cafeteria.asyncio.callbacks import CallbackRegistry, CallbackType

from aiographql.client.exceptions import (
    GraphQLClientException,
    GraphQLClientValidationException,
    GraphQLIntrospectionException,
    GraphQLRequestException,
)
from aiographql.client.helpers import aiohttp_client_session
from aiographql.client.request import GraphQLRequest
from aiographql.client.response import GraphQLResponse
from aiographql.client.subscription import (
    CallbacksType,
    GraphQLSubscription,
    GraphQLSubscriptionEventType,
)


@dataclass(frozen=True)
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
    """

    def __init__(
        self,
        endpoint: str,
        headers: Optional[Mapping[str, str]] = None,
        method: Optional[str] = None,
        schema: Optional[graphql.GraphQLSchema] = None,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> None:
        self.endpoint = endpoint
        self._method = method or GraphQLQueryMethod.post
        self._headers = {"Content-Type": "application/json", "Accept-Encoding": "gzip"}
        self._headers.update(headers or dict())
        self._schema = schema
        self._session = session

    async def introspect(
        self, headers: Optional[Dict[str, str]] = None
    ) -> graphql.GraphQLSchema:
        """
        Introspect the GraphQL endpoint specified for this client and return a `graphql.GraphQLSchema` object
        specifying the schema associated with this endpoint.

        :return: GraphQL schema for the configured endpoint
        """
        request = GraphQLRequest(
            query=graphql.get_introspection_query(descriptions=False),
            validate=False,
            headers=headers,
        )
        introspection = await self.query(request)
        try:
            return graphql.build_client_schema(introspection=introspection.data)
        except TypeError:
            raise GraphQLIntrospectionException(
                f"Failed to build schema from introspection data: {introspection.errors}"
            )

    async def get_schema(
        self, refresh: bool = False, headers: Optional[Dict[str, str]] = None
    ) -> graphql.GraphQLSchema:
        """
        Get the introspected schema for the endpoint used by this client. If an unexpired cache exists, this is
        returned unless the `refresh` parameter is set to True.

        :param refresh: Refresh the cached schema by forcing an introspection of the GraphQL endpoint.
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
        schema: Optional[graphql.GraphQLSchema] = None,
        headers: Optional[Dict[str, str]] = None,
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
        if not request.validate and not force:
            # skip validation if request validate flag is set to false
            return

        schema = schema or await self.get_schema(headers=headers or request.headers)
        errors = await asyncio.get_running_loop().run_in_executor(
            None, graphql.validate, schema, graphql.parse(request.query)
        )
        if errors:
            raise GraphQLClientValidationException(*errors)

    def _prepare_request(
        self,
        request: Union[GraphQLRequest, str],
        operation: Optional[str] = None,
        variables: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
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
            request = GraphQLRequest(query=request)

        return request.copy(
            headers=headers,
            headers_fallback=self._headers,
            operation=operation,
            variables=variables,
        )

    async def _http_request(
        self,
        session: aiohttp.ClientSession,
        method: str,
        request: GraphQLRequest,
        **kwargs: Any,
    ):
        """
        Helper method to make an http request using the provided *session*.

        :param session: Session to use when making the request.
        :param method: HTTP method to use when making the request.
        :param request: Prepared GraphQL request to dispatch to the server.
        :param kwargs: Additional arguments to pass to
            :method:`aiohttp.ClientSession.request` when making the request.
        :raises: :class:`GraphQLRequestException` when the server responds with a
            non 200 status code.
        :return: Query response.
        """
        async with session.request(
            method=method, url=self.endpoint, headers=request.headers, **kwargs
        ) as resp:
            body = await resp.json()
            response = GraphQLResponse(request=request, json=body)

            if 200 <= resp.status < 300:
                return response

            raise GraphQLRequestException(response)

    async def query(
        self,
        request: Union[GraphQLRequest, str],
        method: str = None,
        headers: Optional[Dict[str, str]] = None,
        operation: Optional[str] = None,
        variables: Optional[Dict[str, Any]] = None,
        session: Optional[aiohttp.ClientSession] = None,
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

        if method == GraphQLQueryMethod.post:
            kwargs = dict(json=request.payload())
        elif method == GraphQLQueryMethod.get:
            kwargs = dict(params=request.payload(coerce=True))
        else:
            raise GraphQLClientException(f"Invalid method ({method}) specified")

        if session or self._session:
            return await self._http_request(
                session=session or self._session,
                method=method,
                request=request,
                **kwargs,
            )

        async with aiohttp_client_session() as session:
            return await self._http_request(
                session=session, method=method, request=request, **kwargs
            )

    async def post(
        self,
        request: GraphQLRequest,
        headers: Optional[Dict[str, str]] = None,
        operation: Optional[str] = None,
        variables: Optional[Dict[str, Any]] = None,
        session: Optional[aiohttp.ClientSession] = None,
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
        headers: Optional[Dict[str, str]] = None,
        operation: Optional[str] = None,
        variables: Optional[Dict[str, Any]] = None,
        session: Optional[aiohttp.ClientSession] = None,
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
        headers: Optional[Dict[str, str]] = None,
        operation: Optional[str] = None,
        variables: Optional[Dict[str, Any]] = None,
        callbacks: Optional[CallbacksType] = None,
        on_data: Optional[CallbackType] = None,
        on_error: Optional[CallbackType] = None,
        session: Optional[aiohttp.ClientSession] = None,
        wait: bool = False,
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
        :return: The initialised subscription.
        """
        request = self._prepare_request(
            request=request, operation=operation, variables=variables, headers=headers
        )
        await self.validate(request=request)

        callbacks = callbacks or CallbackRegistry()
        if on_data:
            callbacks.register(GraphQLSubscriptionEventType.DATA, on_data)
        if on_error:
            callbacks.register(GraphQLSubscriptionEventType.ERROR, on_error)

        subscription = GraphQLSubscription(request=request, callbacks=callbacks)
        await subscription.subscribe(
            endpoint=self.endpoint, session=session or self._session, wait=wait
        )
        return subscription
