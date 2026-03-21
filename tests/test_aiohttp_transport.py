from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock
from unittest.mock import MagicMock

import aiohttp
import pytest

from aiographql.client.exceptions import GraphQLClientException
from aiographql.client.request import GraphQLRequest
from aiographql.client.serializer import DefaultSerializer
from aiographql.client.serializer import JSONSerializer
from aiographql.client.transport.aiohttp import AiohttpTransport
from aiographql.client.transport.aiohttp import AiohttpWebSocketResponse


@pytest.mark.asyncio
async def test_aiohttp_transport_invalid_json_response() -> None:
    transport = AiohttpTransport(endpoint="http://test.com")
    request = GraphQLRequest(query="{ test }")
    serializer = DefaultSerializer()

    mock_session = MagicMock(spec=aiohttp.ClientSession)
    mock_resp = MagicMock()
    mock_resp.status = 200

    async def async_read() -> bytes:
        return b"invalid json"

    mock_resp.read = async_read

    class AsyncContextManager:
        async def __aenter__(self) -> Any:
            return mock_resp

        async def __aexit__(self, *args: Any) -> None:
            pass

    mock_session.request.return_value = AsyncContextManager()

    resp = await transport._http_request(mock_session, "POST", request, serializer)
    assert resp.json is None


@pytest.mark.asyncio
async def test_aiohttp_transport_coerce_value_async() -> None:
    transport = AiohttpTransport(endpoint="http://test.com")
    serializer = DefaultSerializer()

    assert transport._coerce_value(True, serializer) == 1
    assert transport._coerce_value(False, serializer) == 0
    assert transport._coerce_value({"a": 1}, serializer) == '{"a":1}'
    assert transport._coerce_value([1, 2], serializer) == "[1,2]"
    assert transport._coerce_value("string", serializer) == "string"


@pytest.mark.asyncio
async def test_aiohttp_transport_invalid_method_async() -> None:
    transport = AiohttpTransport(endpoint="http://test")
    with pytest.raises(GraphQLClientException, match="Invalid method"):
        await transport.request(
            "INVALID", GraphQLRequest(query="{test}"), DefaultSerializer()
        )


def test_aiohttp_transport_coerce_value_extra() -> None:
    transport = AiohttpTransport(endpoint="http://localhost")
    serializer = JSONSerializer()

    # Test boolean coercion
    assert transport._coerce_value(True, serializer) == 1
    assert transport._coerce_value(False, serializer) == 0

    # Test dict/list coercion
    data_dict = {"a": 1}
    coerced_dict = transport._coerce_value(data_dict, serializer)
    assert coerced_dict == '{"a": 1}'

    data_list = [1, 2]
    coerced_list = transport._coerce_value(data_list, serializer)
    assert coerced_list == "[1, 2]"


@pytest.mark.asyncio
async def test_aiohttp_websocket_response_anext() -> None:
    # Mocking aiohttp.ClientWebSocketResponse
    ws = AsyncMock()

    # Mocking WS messages
    msg_text = MagicMock()
    msg_text.type = aiohttp.WSMsgType.TEXT
    msg_text.data = '{"data": "test"}'

    msg_close = MagicMock()
    msg_close.type = aiohttp.WSMsgType.CLOSE

    msg_binary = '{"data": "binary"}'  # simulate non-aiohttp object message

    ws.receive.side_effect = [msg_text, msg_binary, msg_close]

    resp = AiohttpWebSocketResponse(ws)

    # 1st message: TEXT
    assert await resp.__anext__() == '{"data": "test"}'

    # 2nd message: non-aiohttp object
    assert await resp.__anext__() == '{"data": "binary"}'

    # 3rd message: CLOSE
    with pytest.raises(StopAsyncIteration):
        await resp.__anext__()
