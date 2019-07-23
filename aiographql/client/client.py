from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from typing import Dict, List, Optional, Mapping

import aiohttp
import graphql
from cafeteria.asyncio.callbacks import CallbackRegistry, SimpleTriggerCallback

from aiographql.client.exceptions import (
    GraphQLClientException,
    GraphQLClientValidationException,
    GraphQLTransactionException,
    GraphQLIntrospectionException,
)
from aiographql.client.subscription import (
    GraphQLSubscription,
    GraphQLSubscriptionEventType,
)
from aiographql.client.transaction import GraphQLRequest, GraphQLTransaction


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
        self._schema: Optional[graphql.GraphQLSchema] = None

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
        query: str,
        schema: Optional[graphql.GraphQLSchema] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> List[graphql.GraphQLError]:
        return await asyncio.get_running_loop().run_in_executor(
            None,
            graphql.validate,
            schema or await self.get_schema(headers=headers),
            graphql.parse(query),
        )

    async def _validate(
        self, request: GraphQLRequest, headers: Optional[Dict[str, str]] = None
    ):
        if request.validate:
            errors = await self.validate(request.query, request.schema, headers=headers)
            if request.schema is None:
                request.schema = await self.get_schema(headers=headers)
            if errors:
                raise GraphQLClientValidationException(*errors)

    async def request(
        self,
        request: GraphQLRequest,
        method: str = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> GraphQLTransaction:
        headers = {**self._headers, **request.headers, **(headers or dict())}
        await self._validate(request=request, headers=headers)
        method = method or self._method

        if method == QueryMethod.post:
            kwargs = dict(data=json.dumps(request.asdict()))
        elif method == QueryMethod.get:
            params = request.asdict()
            for item in params:
                if isinstance(params[item], bool):
                    params[item] = int(params[item])
                if isinstance(params[item], dict):
                    params[item] = str(params[item])
            kwargs = dict(params=params)
        else:
            raise GraphQLClientException(f"Invalid method ({method}) specified")

        async with aiohttp.ClientSession(
            headers={**self._headers, **request.headers, **headers}
        ) as session:
            async with session.request(method, self.endpoint, **kwargs) as resp:
                body = await resp.json()
                transaction = GraphQLTransaction.create(request=request, json=body)

                if 200 <= resp.status < 300:
                    return transaction

                raise GraphQLTransactionException(transaction)

    async def post(
        self, request: GraphQLRequest, headers: Optional[Dict[str, str]] = None
    ) -> GraphQLTransaction:
        return await self.request(request, method=QueryMethod.post, headers=headers)

    async def get(
        self, request: GraphQLRequest, headers: Optional[Dict[str, str]] = None
    ) -> GraphQLTransaction:
        return await self.request(request, method=QueryMethod.get, headers=headers)

    async def query(
        self, request: GraphQLRequest, headers: Optional[Dict[str, str]] = None
    ) -> GraphQLTransaction:
        return await self.request(request=request, headers=headers)

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
        headers: Optional[Dict[str, str]] = None,
    ) -> GraphQLSubscription:
        await self._validate(request, headers=headers)
        headers = headers or {}
        subscription = GraphQLSubscription(
            request=request,
            callbacks=callbacks or CallbackRegistry(),
            headers={**self._headers, **request.headers, **headers},
        )
        subscription.task = asyncio.create_task(self._subscribe(subscription))
        return subscription
