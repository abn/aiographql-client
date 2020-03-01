from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, NoReturn, Optional, Union

import aiohttp
from cafeteria.asyncio.callbacks import (
    CallbackRegistry,
    CallbackType,
    SimpleTriggerCallback,
)

from aiographql.client.helpers import create_default_connector
from aiographql.client.request import GraphQLRequestContainer
from aiographql.client.response import GraphQLBaseResponse, GraphQLResponse


class GraphQLSubscriptionEventType(Enum):
    CONNECTION_INIT = "connection_init"
    CONNECTION_ACK = "connection_ack"
    CONNECTION_ERROR = "connection_error"
    CONNECTION_TERMINATE = "connection_terminate"
    START = "start"
    DATA = "data"
    ERROR = "error"
    COMPLETE = "complete"
    STOP = "stop"
    KEEP_ALIVE = "ka"


CallbacksType = Union[
    CallbackRegistry,
    Dict[GraphQLSubscriptionEventType, Union[CallbackType, List[CallbackType]]],
]


@dataclass(frozen=True)
class GraphQLSubscriptionEvent(GraphQLBaseResponse):
    subscription_id: Optional[str] = field(default=None)

    @property
    def id(self) -> Optional[str]:
        return self.json.get("id")

    @property
    def type(self) -> Optional[GraphQLSubscriptionEventType]:
        try:
            return GraphQLSubscriptionEventType(self.json.get("type"))
        except ValueError:
            pass

    @property
    def payload(self) -> Optional[Union[GraphQLResponse, str]]:
        payload = self.json.get("payload")
        if payload is not None:
            if self.type in (
                GraphQLSubscriptionEventType.DATA,
                GraphQLSubscriptionEventType.ERROR,
            ):
                return GraphQLResponse(request=self.request, json=payload)
            return payload


@dataclass(frozen=True)
class GraphQLSubscription(GraphQLRequestContainer):
    """
    Subscription container, with an attached :class:`CallbackRegistry`. When subscribed,
    the `task` will be populated with the :class:`asyncio.Task` instance.

    By default the subscription will be stopped, if an error, connection error or
    complete (:class:`GraphQLSubscriptionEventType`) is received.

    Subscription instances are intended to be used as immutable objects. However,
    `callbacks` and `stop_event_types` can be updated after initialisation.
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()), init=False)
    callbacks: Optional[CallbacksType] = field(default_factory=CallbackRegistry)
    stop_event_types: List[GraphQLSubscriptionEventType] = field(
        default_factory=lambda: [
            GraphQLSubscriptionEventType.ERROR,
            GraphQLSubscriptionEventType.CONNECTION_ERROR,
            GraphQLSubscriptionEventType.COMPLETE,
        ]
    )
    task: asyncio.Task = field(default=None, init=False, compare=False)

    def active(self) -> bool:
        """
        Check if the subscription is active.

        :return: `True` if subscribed and active.
        """
        return (
            self.task is not None and not self.task.done() and not self.task.cancelled()
        )

    def connection_init_request(self) -> Dict[str, Any]:
        """
        Connection init payload to use when initiating a new subscription.

        :return: Connection initialise payload.
        """
        return {
            "type": GraphQLSubscriptionEventType.CONNECTION_INIT.value,
            "payload": {"headers": {**self.request.headers}},
        }

    def connection_start_request(self) -> Dict[str, Any]:
        """
        Connection start payload to use when starting a subscription.

        :return: Connection start payload.
        """
        return {
            "id": self.id,
            "type": GraphQLSubscriptionEventType.START.value,
            "payload": self.request.payload(),
        }

    def connection_stop_request(self) -> Dict[str, Any]:
        """
        Connection stop payload to use when stopping a subscription.

        :return: Connection stop payload.
        """
        return {"id": self.id, "type": GraphQLSubscriptionEventType.STOP.value}

    def is_stop_event(self, event: GraphQLSubscriptionEvent) -> bool:
        """
        Check if the provided *event* is configured as a stop even for this subscription.

        :param event: Event to check.
        :return: `True` if `event` is in `stop_event_types`.
        """
        return event.type in self.stop_event_types

    async def handle(self, event: GraphQLSubscriptionEvent) -> NoReturn:
        """
        Helper method to dispatch any configured callbacks for the specified event type.

        :param event: Event to dispatch callbacks for.
        """
        if event.id is None or event.id == self.id:
            await self.callbacks.handle_event(event.type, event)

    async def _websocket_connect(
        self, endpoint: str, session: aiohttp.ClientSession
    ) -> None:
        """
        Helper method to create websocket connection with specified *endpoint*
        using the specified :class:`aiohttp.ClientSession`. Once connected, we
        initialise and start the GraphQL subscription; then wait for any incoming
        messages. Any message received via the websocket connection is cast into
        a :class:`GraphQLSubscriptionEvent` instance and dispatched for handling via
        :method:`handle`.

        :param endpoint: Endpoint to use when creating the websocket connection.
        :param session: Session to use when creating the websocket connection.
        """
        async with session.ws_connect(endpoint) as ws:
            await ws.send_json(data=self.connection_init_request())

            self.callbacks.register(
                GraphQLSubscriptionEventType.CONNECTION_ACK,
                SimpleTriggerCallback(
                    function=ws.send_json, data=self.connection_start_request()
                ),
            )

            try:
                async for msg in ws:  # type:  aiohttp.WSMessage
                    if msg.type != aiohttp.WSMsgType.TEXT:
                        if msg.type == aiohttp.WSMsgType.ERROR:
                            break
                        continue

                    event = GraphQLSubscriptionEvent(
                        subscription_id=self.id, request=self.request, json=msg.json(),
                    )
                    await self.handle(event=event)

                    if self.is_stop_event(event):
                        break
            except (asyncio.CancelledError, KeyboardInterrupt):
                await ws.send_json(data=self.connection_stop_request())

    async def _subscribe(
        self, endpoint: str, session: Optional[aiohttp.ClientSession] = None
    ) -> None:
        """
        Helper method wrapping :method:`GraphQLSubscription._websocket_connect` handling
        unique :class:`aiohttp.ClentSession` creation if on is not already provided.

        :param endpoint: Endpoint to use when creating the websocket connection.
        :param session: Optional session to use when creating the websocket connection.
        """
        if session:
            return await self._websocket_connect(endpoint=endpoint, session=session)

        connector = await create_default_connector()
        async with aiohttp.ClientSession(connector=connector) as session:
            return await self._websocket_connect(endpoint=endpoint, session=session)

    async def subscribe(
        self,
        endpoint: str,
        force: bool = False,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> None:
        """
        Create a websocket subscription and set internal task.

        :param endpoint: GraphQL endpoint to subscribe to
        :param force: Force re-subscription if already subscribed
        :param session: Optional session to use for requests
        """
        if self.active() and not force:
            return
        self.unsubscribe()
        task = asyncio.create_task(self._subscribe(endpoint=endpoint, session=session))
        object.__setattr__(self, "task", task)

    def unsubscribe(self) -> None:
        """
        Unsubscribe current websocket subscription if active and clear internal task.
        """
        if self.active():
            try:
                self.task.cancel()
            except asyncio.CancelledError:
                pass
        object.__setattr__(self, "task", None)
