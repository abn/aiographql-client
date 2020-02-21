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
from aiographql.client.helpers import create_default_connector
from aiographql.client.subscription import (
    GraphQLSubscription,
    GraphQLSubscriptionEventType,
)
from aiographql.client.transaction import GraphQLRequest, GraphQLResponse


@dataclass(frozen=True)
class QueryMethod:
    post: str = "post"
    get: str = "get"


class GraphQLClient:
    def __init__(
        self,
        endpoint: str,
        headers: Optional[Mapping[str, str]] = None,
        method: Optional[str] = None,
        schema: Optional[graphql.GraphQLSchema] = None,
    ) -> None:
        """
        Initialise a GraphQL Client

        :param endpoint: URI of graph api.
        :param headers: Default headers to use for every request made by this client.
            By default the client adds 'Content-Type: application/json' and
            'Accept-Encoding: gzip' to all requests. These can be overridden by
            specifying then here.
        :param method: Default method to use when submitting a GraphQL request to the
            specified `endpoint`.
        """
        self.endpoint = endpoint
        self._method = method or QueryMethod.post
        self._headers = {"Content-Type": "application/json", "Accept-Encoding": "gzip"}
        self._headers.update(headers or dict())
        self._schema = schema

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
        Helper method to ensure that queries handle both string and `GraphQLRequest`
        objects.

        :param request:
        :param operation:
        :param variables:
        :param headers:
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
        Method to send provided `GraphQLRequest` to the configured endpoint as an
        HTTP request. This method handles the configuration of headers HTTP method
        specific handling of request parameters and/or data as required.

        The order of precedence, least to greatest, of headers is as follows,
            1. client headers (`GraphQLClient.headers`)
            2. request headers (`GraphQLRequest.headers`)
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
        :return: The resulting transaction object.
        """
        request = self._prepare_request(
            request=request, operation=operation, variables=variables, headers=headers
        )

        await self.validate(request=request)
        method = method or self._method

        if method == QueryMethod.post:
            kwargs = dict(json=request.payload())
        elif method == QueryMethod.get:
            kwargs = dict(params=request.payload(coerce=True))
        else:
            raise GraphQLClientException(f"Invalid method ({method}) specified")

        if session:
            return await self._http_request(
                session=session, method=method, request=request, **kwargs
            )

        connector = await create_default_connector()
        async with aiohttp.ClientSession(connector=connector) as session:
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
        `QueryMethod.POST`.
        """
        return await self.query(
            request,
            method=QueryMethod.post,
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
        Helper method that wraps `GraphQLClient.query` with method explicitly set as
        `QueryMethod.GET`.
        """
        return await self.query(
            request,
            method=QueryMethod.get,
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
        callbacks: Optional[CallbackRegistry] = None,
        on_data: Optional[CallbackType] = None,
        on_error: Optional[CallbackType] = None,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> GraphQLSubscription:
        request = self._prepare_request(
            request=request, operation=operation, variables=variables, headers=headers
        )
        await self.validate(request=request)

        callbacks = callbacks or CallbackRegistry()
        if on_data:
            callbacks.register(GraphQLSubscriptionEventType.DATA, on_data)
        if on_error:
            callbacks.register(GraphQLSubscriptionEventType.ERROR, on_error)

        subscription = GraphQLSubscription(
            request=request, callbacks=callbacks or CallbackRegistry()
        )
        subscription.subscribe(endpoint=self.endpoint, session=session)
        return subscription
