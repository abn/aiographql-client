from __future__ import annotations

import asyncio
import json
from typing import Dict, Any, Optional, List

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
from aiographql.client.transaction import (
    GraphQLTransaction,
    GraphQLResponse,
    GraphQLRequest,
)

QUERY_METHOD_POST = "post"
QUERY_METHOD_GET = "get"


class GraphQLClient:
    def __init__(self, endpoint, headers=None, method=QUERY_METHOD_POST):
        self.endpoint = endpoint
        self._method = method
        self._headers = {"Content-Type": "application/json", "Accept-Encoding": "gzip"}
        self._headers.update(headers or dict())
        self._connector = aiohttp.TCPConnector(ttl_dns_cache=60)
        self._schema: Optional[graphql.GraphQLSchema] = None
        asyncio.create_task(self.introspect())

    @property
    def schema(self):
        # TODO: consider adding ttl logic for expiring schemas for long running services
        return self._schema

    async def introspect(self):
        introspection = await self.query(
            query=graphql.get_introspection_query(descriptions=False), validate=False
        )
        self._schema = graphql.build_client_schema(introspection=introspection.data)

    async def validate(self, query) -> List[graphql.GraphQLError]:
        if self.schema is None:
            await self.introspect()
        return await asyncio.get_running_loop().run_in_executor(
            None, graphql.validate, self.schema, graphql.parse(query)
        )

    async def _validate(self, query: str, validate: bool = True):
        if validate:
            errors = await self.validate(query)
            if errors:
                raise GraphQLClientValidationException(*errors)

    async def request(
        self, request: GraphQLRequest, validate: bool = True, method: str = None
    ) -> GraphQLTransaction:
        await self._validate(request.query, validate)
        method = method or self._method

        if method == QUERY_METHOD_POST:
            kwargs = dict(data=json.dumps(request.json()))
        elif method == QUERY_METHOD_GET:
            kwargs = dict(params=request.json())
        else:
            raise GraphQLClientException(f"Invalid method ({method}) specified")

        async with aiohttp.ClientSession(headers=self._headers) as session:
            async with session.request(method, self.endpoint, **kwargs) as resp:
                body = await resp.json()
                transaction = GraphQLTransaction(
                    request=request, response=GraphQLResponse(json=body)
                )

                if 200 <= resp.status < 300:
                    return transaction

                raise GraphQLTransactionException(transaction)

    async def post(
        self, request: GraphQLRequest, validate: bool = True
    ) -> GraphQLTransaction:
        return await self.request(request, validate, QUERY_METHOD_POST)

    async def get(
        self, request: GraphQLRequest, validate: bool = True
    ) -> GraphQLTransaction:
        return await self.request(request, validate, QUERY_METHOD_GET)

    async def query(
        self,
        query: str,
        variables: Optional[Dict[str, Any]] = None,
        operation_name: Optional[str] = None,
        validate: bool = True,
    ) -> GraphQLTransaction:
        request = GraphQLRequest(
            query=query, variables=variables, operationName=operation_name
        )
        return await self.request(request=request, validate=validate)

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
        self,
        request: GraphQLRequest,
        callbacks: Optional[CallbackRegistry] = None,
        validate: bool = True,
    ) -> GraphQLSubscription:
        await self._validate(request.query, validate)
        subscription = GraphQLSubscription(
            request=request, callbacks=callbacks or CallbackRegistry()
        )
        subscription.headers.update(**self._headers)
        subscription.task = asyncio.create_task(self._subscribe(subscription))
        return subscription
