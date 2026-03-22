from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Any
from typing import cast
from unittest.mock import MagicMock

import pytest

from aiographql.client.request import GraphQLRequest
from aiographql.client.subscription import GraphQLSubscription
from aiographql.client.subscription import GraphQLSubscriptionEventType
from aiographql.client.transport.base import GraphQLSubscriptionTransport
from aiographql.client.transport.base import GraphQLWebSocketResponse


pytestmark = pytest.mark.asyncio


if TYPE_CHECKING:
    from cafeteria.asyncio.callbacks import CallbackRegistry

    from aiographql.client.response import GraphQLResponse


class MockWebSocketResponse(GraphQLWebSocketResponse):
    def __init__(self, messages: list[str]) -> None:
        self.messages = messages
        self.sent: list[str] = []
        self.closed = False

    async def __aenter__(self) -> MockWebSocketResponse:
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.closed = True

    async def send_str(self, data: str) -> None:
        self.sent.append(data)

    def __aiter__(self) -> MockWebSocketResponse:
        return self

    async def __anext__(self) -> str:
        if not self.messages:
            raise StopAsyncIteration
        return self.messages.pop(0)


async def test_subscription_handle_server_error(ws_message_error: str) -> None:
    req = GraphQLRequest(query="subscription { city { name } }")
    # subscription ID is normally a UUID, let's fix it for the test
    sub = GraphQLSubscription(request=req)
    sub_id = "test-subscription-id"
    object.__setattr__(sub, "id", sub_id)

    # Ensure the message ID matches the subscription ID
    import json

    msg = json.loads(ws_message_error)
    msg["id"] = sub_id
    ws_message_error_matching = json.dumps(msg)

    mock_transport = MagicMock(spec=GraphQLSubscriptionTransport)
    mock_ws = MockWebSocketResponse([ws_message_error_matching])
    mock_transport.subscribe.return_value = mock_ws

    # Setup callbacks to verify dispatch
    mock_on_error = MagicMock()
    # Use the Enum member as the key
    registry = cast("CallbackRegistry", sub.callbacks)
    registry.register(GraphQLSubscriptionEventType.ERROR, mock_on_error)

    # Run _websocket_connect
    await sub._websocket_connect("ws://test", mock_transport)

    mock_on_error.assert_called_once()
    from aiographql.client.subscription import GraphQLSubscriptionEvent

    event = cast("GraphQLSubscriptionEvent", mock_on_error.call_args[0][0])
    assert event.type == GraphQLSubscriptionEventType.ERROR
    assert cast("GraphQLResponse", event.payload).json["message"] == "an error occurred"


async def test_subscription_handle_invalid_json(ws_message_invalid_json: str) -> None:
    req = GraphQLRequest(query="subscription { city { name } }")
    sub = GraphQLSubscription(request=req)

    mock_transport = MagicMock(spec=GraphQLSubscriptionTransport)
    # The subscription loop should probably not crash on invalid JSON,
    # but currently it might if loads() raises.
    # Let's see what happens.
    mock_ws = MockWebSocketResponse([ws_message_invalid_json])
    mock_transport.subscribe.return_value = mock_ws

    # If it raises, we might want to catch it or ensure it's handled.
    # Based on _websocket_connect code, it calls serializer.loads(data) directly.
    # DefaultSerializer.loads uses orjson.loads which raises orjson.JSONDecodeError

    with pytest.raises(
        Exception, match="unexpected end of data"
    ):  # orjson.JSONDecodeError
        await sub._websocket_connect("ws://test", mock_transport)


async def test_subscription_complete_breaks_loop(ws_message_complete: str) -> None:
    req = GraphQLRequest(query="subscription { city { name } }")
    sub = GraphQLSubscription(request=req)

    mock_transport = MagicMock(spec=GraphQLSubscriptionTransport)
    # complete message should break the loop
    mock_ws = MockWebSocketResponse([ws_message_complete, '{"type":"data"}'])
    mock_transport.subscribe.return_value = mock_ws

    await sub._websocket_connect("ws://test", mock_transport)

    # If it broke correctly, it should only have consumed the complete message
    assert len(mock_ws.messages) == 1
    assert mock_ws.messages[0] == '{"type":"data"}'
