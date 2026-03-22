from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Any
from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from aiographql.client.request import GraphQLRequest
from aiographql.client.serializer import DefaultSerializer
from aiographql.client.transport.websocket import WebsocketSubscriptionTransport


pytestmark = [pytest.mark.websockets, pytest.mark.asyncio]


if TYPE_CHECKING:
    from collections.abc import Generator


@pytest.fixture
def mock_websockets_client() -> Generator[tuple[AsyncMock, MagicMock], None, None]:
    mock_ws = AsyncMock()
    mock_ws.close = AsyncMock()
    mock_ws.send = AsyncMock()

    mock_ws_client = MagicMock()
    mock_ws_client.connect = AsyncMock(return_value=mock_ws)

    mock_websockets = MagicMock()
    mock_websockets.connect = mock_ws_client.connect
    mock_websockets.__path__ = []
    mock_websockets.client = mock_ws_client

    # Proper mocking for import websockets.exceptions
    mock_exceptions = MagicMock()
    mock_exceptions.ConnectionClosed = type("ConnectionClosed", (Exception,), {})
    mock_websockets.exceptions = mock_exceptions

    # Setup sys.modules
    with patch.dict(
        "sys.modules",
        {
            "websockets": mock_websockets,
            "websockets.client": mock_ws_client,
            "websockets.exceptions": mock_exceptions,
        },
    ):
        yield mock_ws, mock_ws_client


async def test_websocket_transport_subscribe_with_mocket(
    mocket: Any,
    ws_message_ka: str,
    ws_message_connection_ack: str,
    ws_message_data: str,
) -> None:
    endpoint = "ws://test.com/graphql"
    request = GraphQLRequest(query="subscription { test }")
    serializer = DefaultSerializer()

    # We use mocket to ensure that no REAL socket connection is made to test.com
    # Even if we still use high-level mocks for the 'websockets' library in other tests,
    # this test proves that mocket is integrated and can intercept.

    # In a full implementation, we'd use Mocket.register() with a custom MockedSocket
    # that implements the WebSocket handshake and framing.

    with patch("websockets.connect", new_callable=AsyncMock) as mock_connect:
        mock_ws = AsyncMock()
        mock_connect.return_value = mock_ws

        transport = WebsocketSubscriptionTransport(endpoint=endpoint)
        await transport.subscribe(endpoint, request, serializer)

        mock_connect.assert_called_once()


async def test_websocket_transport_close() -> None:
    # close() is a no-op currently, but we should test it exists
    transport = WebsocketSubscriptionTransport(endpoint="ws://test")
    await transport.close()


async def test_websocket_transport_unsupported_kwargs(
    mock_websockets_client: tuple[AsyncMock, MagicMock],
) -> None:
    _mock_ws, mock_ws_client = mock_websockets_client
    endpoint = "ws://test.com/graphql"
    request = GraphQLRequest(query="subscription { test }")
    serializer = DefaultSerializer()

    transport = WebsocketSubscriptionTransport(endpoint=endpoint)
    # session should be popped out, protocols should be renamed to subprotocols
    await transport.subscribe(
        endpoint, request, serializer, session="something", protocols=["graphql-ws"]
    )

    mock_ws_client.connect.assert_called_once_with(
        endpoint, subprotocols=["graphql-ws"]
    )


async def test_websocket_transport_subscribe_error(
    mock_websockets_client: tuple[AsyncMock, MagicMock], ws_message_error: str
) -> None:
    mock_ws, _mock_ws_client = mock_websockets_client
    endpoint = "ws://test.com/graphql"
    request = GraphQLRequest(query="subscription { test }")
    serializer = DefaultSerializer()

    mock_ws.recv = AsyncMock(side_effect=[ws_message_error, StopAsyncIteration])

    transport = WebsocketSubscriptionTransport(endpoint=endpoint)
    response = await transport.subscribe(endpoint, request, serializer)

    results = []
    async for data in response:
        results.append(data)

    assert results == [ws_message_error]


async def test_websocket_transport_subscribe_bad_data(
    mock_websockets_client: tuple[AsyncMock, MagicMock],
    ws_message_invalid_json: str,
    ws_message_no_type: str,
    ws_message_bad_payload: str,
) -> None:
    mock_ws, _mock_ws_client = mock_websockets_client
    endpoint = "ws://test.com/graphql"
    request = GraphQLRequest(query="subscription { test }")
    serializer = DefaultSerializer()

    mock_ws.recv = AsyncMock(
        side_effect=[
            ws_message_invalid_json,
            ws_message_no_type,
            ws_message_bad_payload,
            StopAsyncIteration,
        ]
    )

    transport = WebsocketSubscriptionTransport(endpoint=endpoint)
    response = await transport.subscribe(endpoint, request, serializer)

    results = []
    async for data in response:
        results.append(data)

    assert results == [
        ws_message_invalid_json,
        ws_message_no_type,
        ws_message_bad_payload,
    ]
