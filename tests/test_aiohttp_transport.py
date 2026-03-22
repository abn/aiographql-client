from __future__ import annotations

import asyncio

from typing import TYPE_CHECKING
from typing import Any
from typing import TypeVar

import pytest

from mocket.plugins.httpretty import HTTPretty

from aiographql.client.exceptions import GraphQLClientException
from aiographql.client.exceptions import GraphQLTransportException
from aiographql.client.request import GraphQLRequest
from aiographql.client.serializer import DefaultSerializer
from aiographql.client.serializer import JSONSerializer
from aiographql.client.transport.aiohttp import AiohttpTransport
from aiographql.client.transport.aiohttp import AiohttpWebSocketResponse


if TYPE_CHECKING:
    from collections.abc import Callable
    from collections.abc import Coroutine


T = TypeVar("T")

pytestmark = [pytest.mark.aiohttp, pytest.mark.asyncio]


async def retry_on_transport_error(
    func: Callable[..., Coroutine[Any, Any, T]],
    retries: int = 3,
    delay: float = 1.0,
    *args: Any,
    **kwargs: Any,
) -> T:
    for i in range(retries):
        try:
            return await func(*args, **kwargs)
        except GraphQLTransportException:
            if i == retries - 1:
                raise
            await asyncio.sleep(delay)
    raise RuntimeError("Unreachable")


@pytest.mark.strawberry
async def test_aiohttp_transport_session_override(
    strawberry_server: str,
) -> None:
    endpoint = strawberry_server
    import aiohttp

    async with aiohttp.ClientSession() as session:
        transport = AiohttpTransport(endpoint=endpoint)
        serializer = DefaultSerializer()
        request = GraphQLRequest(
            query="{ hello }", headers={"Content-Type": "application/json"}
        )

        # Pass session as an override in the request call
        response = await retry_on_transport_error(
            transport.request,
            method="POST",
            request=request,
            serializer=serializer,
            session=session,
        )
        assert response.data == {"hello": "world"}

        await transport.close()
        # session should NOT be closed if it was provided by the user
        assert not session.closed


async def test_aiohttp_transport_external_session(
    strawberry_server: str,
) -> None:
    endpoint = strawberry_server
    import aiohttp

    async with aiohttp.ClientSession() as session:
        transport = AiohttpTransport(endpoint=endpoint, session=session)
        serializer = DefaultSerializer()
        request = GraphQLRequest(
            query="{ hello }", headers={"Content-Type": "application/json"}
        )

        response = await retry_on_transport_error(
            transport.request, method="POST", request=request, serializer=serializer
        )
        assert response.data == {"hello": "world"}

        await transport.close()
        # session should NOT be closed if it was provided by the user
        assert not session.closed


async def test_aiohttp_transport_invalid_json_response(
    mocket: Any, httpretty: Any
) -> None:
    endpoint = "http://test.com/graphql"
    transport = AiohttpTransport(endpoint=endpoint)
    request = GraphQLRequest(query="{ test }")
    serializer = DefaultSerializer()

    httpretty.register_uri(
        HTTPretty.POST,
        endpoint,
        body="invalid json",
        content_type="text/plain",
        status=200,
    )

    resp = await transport.request("POST", request, serializer)
    assert resp.json is None


async def test_aiohttp_transport_coerce_value_async() -> None:
    transport = AiohttpTransport(endpoint="http://test.com")
    serializer = DefaultSerializer()

    assert transport._coerce_value(True, serializer) == 1
    assert transport._coerce_value(False, serializer) == 0
    assert transport._coerce_value({"a": 1}, serializer) == '{"a":1}'
    assert transport._coerce_value([1, 2], serializer) == "[1,2]"
    assert transport._coerce_value("string", serializer) == "string"


async def test_aiohttp_transport_invalid_method_async() -> None:
    transport = AiohttpTransport(endpoint="http://test")
    with pytest.raises(GraphQLClientException, match="Invalid method"):
        await transport.request(
            "INVALID", GraphQLRequest(query="{test}"), DefaultSerializer()
        )


async def test_aiohttp_transport_coerce_value_extra() -> None:
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


async def test_aiohttp_websocket_response_anext() -> None:
    from unittest.mock import AsyncMock
    from unittest.mock import MagicMock

    import aiohttp

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
