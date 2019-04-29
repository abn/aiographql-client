from __future__ import annotations

import asyncio
import json
from typing import Optional, List, Dict

import aiohttp
import graphql
from cafeteria.asyncio.callbacks import CallbackRegistry, SimpleTriggerCallback

from aiographql.client.exceptions import (
    GraphQLClientException,
    GraphQLTransactionException,
    GraphQLClientValidationException,
)
from aiographql.client.subscription import (
    GraphQLSubscriptionEventType,
    GraphQLSubscription,
)
from aiographql.client.transaction import GraphQLTransaction, GraphQLRequest

QUERY_METHOD_POST = "post"
QUERY_METHOD_GET = "get"


class GraphQLClient:
    def __init__(self, endpoint, headers=None, method=QUERY_METHOD_POST):
        self.endpoint = endpoint
        self._method = method
        self._headers = {"Content-Type": "application/json", "Accept-Encoding": "gzip"}
        self._headers.update(headers or dict())
        self._schema: Optional[graphql.GraphQLSchema] = None

    async def introspect(
        self, extra_headers: Optional[Dict[str, str]] = None
    ) -> graphql.GraphQLSchema:
        if extra_headers is None:
            extra_headers = {}
        """
        Introspect the GraphQL endpoint specified for this client and return a `graphql.GraphQLSchema` object
        specifying the schema associated with this endpoint.

        :return: GraphQL schema for the configured endpoint
        """
        request = GraphQLRequest(
            query=graphql.get_introspection_query(descriptions=False),
            validate=False,
            extra_headers=extra_headers,
        )
        introspection = await self.query(request)
        return graphql.build_client_schema(introspection=introspection.data)

    async def get_schema(self, refresh: bool = False) -> graphql.GraphQLSchema:
        """
        Get the introspected schema for the endpoint used by this client. If an unexpired cache exists, this is
        returned unless the `refresh` parameter is set to True.

        :param refresh: Refresh the cached schema by forcing an introspection of the GraphQL endpoint.
        :return: The GraphQL schema as introspected. This maybe a previously cached value.
        """
        # TODO: consider adding ttl logic for expiring schemas for long running services
        if self._schema is None or refresh:
            self._schema = await self.introspect()
        return self._schema

    async def validate(
        self,
        query: str,
        schema: Optional[graphql.GraphQLSchema] = None,
        extra_headers: Optional[Dict[str, str]] = None,
    ) -> List[graphql.GraphQLError]:
        if schema is None:
            if self.schema is None:
                await self.introspect(extra_headers)
            schema = self.schema

        return await asyncio.get_running_loop().run_in_executor(
            None,
            graphql.validate,
            schema or await self.get_schema(),
            graphql.parse(query),
        )

    async def _validate(self, request: GraphQLRequest):
        if request.validate:
            errors = await self.validate(
                request.query, request.schema, extra_headers=request.extra_headers
            )
            if request.schema is None:
                request.schema = await self.get_schema()
            if errors:
                raise GraphQLClientValidationException(*errors)

    async def request(
        self, request: GraphQLRequest, method: str = None
    ) -> GraphQLTransaction:
        await self._validate(request)
        method = method or self._method

        if method == QUERY_METHOD_POST:
            kwargs = dict(data=json.dumps(request.json()))
        elif method == QUERY_METHOD_GET:
            kwargs = dict(params=request.json())
        else:
            raise GraphQLClientException(f"Invalid method ({method}) specified")
        headers = {**self._headers, **request.extra_headers}
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.request(method, self.endpoint, **kwargs) as resp:
                body = await resp.json()
                transaction = GraphQLTransaction.create(request=request, json=body)

                if 200 <= resp.status < 300:
                    return transaction

                raise GraphQLTransactionException(transaction)

    async def post(self, request: GraphQLRequest) -> GraphQLTransaction:
        return await self.request(request, QUERY_METHOD_POST)

    async def get(self, request: GraphQLRequest) -> GraphQLTransaction:
        return await self.request(request, QUERY_METHOD_GET)

    async def query(self, request: GraphQLRequest) -> GraphQLTransaction:
        return await self.request(request=request)

    async def _subscribe(self, subscription: GraphQLSubscription):
        async with aiohttp.ClientSession() as session:
            async with session.ws_connect(self.endpoint) as ws:
                await ws.send_json(data=subscription.connection_init_request)

                subscription.callbacks.register(
                    GraphQLSubscriptionEventType.CONNECTION_ACK,
                    SimpleTriggerCallback(
                        function=ws.send_json,
                        data=subscription.connection_start_request,
                    ),
                )

                try:
                    async for msg in ws:  # type:  aiohttp.WSMessage
                        if msg.type != aiohttp.WSMsgType.TEXT:
                            if msg.type == aiohttp.WSMsgType.ERROR:
                                break
                            continue

                        # noinspection PyTypeChecker,PyNoneFunctionAssignment
                        event = subscription.create_event(msg.json())
                        await subscription.handle(event=event)

                        if subscription.is_stop_event(event):
                            break
                except (asyncio.CancelledError, KeyboardInterrupt):
                    await ws.send_json(data=subscription.connection_stop_request)

    async def subscribe(
        self, request: GraphQLRequest, callbacks: Optional[CallbackRegistry] = None
    ) -> GraphQLSubscription:
        await self._validate(request)
        subscription = GraphQLSubscription(
            request=request, callbacks=callbacks or CallbackRegistry()
        )
        subscription.headers.update(**self._headers)
        subscription.task = asyncio.create_task(self._subscribe(subscription))
        return subscription
