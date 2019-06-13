from __future__ import annotations

import uuid
from asyncio import Task
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, NoReturn, Optional, Union

from cafeteria.asyncio.callbacks import CallbackRegistry

from aiographql.client.transaction import (
    GraphQLBaseResponse,
    GraphQLRequest,
    GraphQLResponse,
)


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


@dataclass
class GraphQLSubscriptionMessage(GraphQLBaseResponse):
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
    def payload(self) -> Union[NoReturn, GraphQLResponse, str]:
        payload = self.json.get("payload")
        if payload is not None:
            if self.type == GraphQLSubscriptionEventType.DATA:
                return GraphQLResponse(request=self.request, json=payload)
            return payload


@dataclass
class GraphQLSubscriptionEvent:
    subscription: GraphQLSubscription
    message: GraphQLSubscriptionMessage

    @property
    def query(self):
        return self.subscription.request.query

    @property
    def id(self):
        return self.message.id

    @property
    def type(self):
        return self.message.type

    @property
    def payload(self):
        return self.message.payload


@dataclass
class GraphQLSubscription:
    request: GraphQLRequest
    callbacks: CallbackRegistry = field(default_factory=CallbackRegistry)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    headers: Dict[str, str] = field(default_factory=dict)
    stop_event_types: List[GraphQLSubscriptionEventType] = field(
        default_factory=lambda: [
            GraphQLSubscriptionEventType.ERROR,
            GraphQLSubscriptionEventType.CONNECTION_ERROR,
            GraphQLSubscriptionEventType.COMPLETE,
        ]
    )
    task: Task = None

    @property
    def is_running(self):
        return (
            self.task is not None and not self.task.done() and not self.task.cancelled()
        )

    @property
    def is_complete(self):
        return self.task is not None and (self.task.done() or self.task.cancelled())

    @property
    def connection_init_request(self):
        return {
            "type": GraphQLSubscriptionEventType.CONNECTION_INIT.value,
            "payload": {"headers": self.headers or self.request.headers},
        }

    @property
    def connection_start_request(self):
        return {
            "id": self.id,
            "type": GraphQLSubscriptionEventType.START.value,
            "payload": self.request.asdict(),
        }

    @property
    def connection_stop_request(self):
        return {"id": self.id, "type": GraphQLSubscriptionEventType.STOP.value}

    def is_stop_event(self, event: GraphQLSubscriptionEvent):
        return event.type in self.stop_event_types

    def create_event(self, message: Dict[str, Any]) -> GraphQLSubscriptionEvent:
        return GraphQLSubscriptionEvent(
            subscription=self,
            message=GraphQLSubscriptionMessage(request=self.request, json=message),
        )

    async def handle(self, event: GraphQLSubscriptionEvent) -> NoReturn:
        if event.id is None or event.id == self.id:
            await self.callbacks.handle_event(event.type, event)
