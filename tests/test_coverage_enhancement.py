from __future__ import annotations

import importlib.metadata

from typing import TYPE_CHECKING
from typing import Any
from typing import cast
from unittest.mock import MagicMock
from unittest.mock import patch

import aiohttp
import httpx
import pytest

from cafeteria.asyncio.callbacks import CallbackRegistry

from aiographql.client.exceptions import GraphQLClientException
from aiographql.client.exceptions import GraphQLRequestException
from aiographql.client.request import GraphQLRequest
from aiographql.client.serializer import DefaultSerializer
from aiographql.client.subscription import GraphQLSubscription
from aiographql.client.subscription import GraphQLSubscriptionEvent
from aiographql.client.subscription import GraphQLSubscriptionEventType
from aiographql.client.transport.base import GraphQLSubscriptionTransport
from aiographql.client.transport.base import GraphQLTransport
from aiographql.client.transport.http import AiohttpTransport
from aiographql.client.transport.http import HttpxTransport
from aiographql.client.transport.resolver import _is_httpx_available
from aiographql.client.transport.resolver import get_default_subscription_transport
from aiographql.client.transport.resolver import get_default_transport


if TYPE_CHECKING:
    from aiographql.client.response import GraphQLResponse


@pytest.mark.asyncio
async def test_httpx_transport_http_error_handling() -> None:
    transport = HttpxTransport(endpoint="http://test.com")
    request = GraphQLRequest(query="{ test }")
    serializer = DefaultSerializer()

    mock_client = MagicMock(spec=httpx.AsyncClient)
    # Simulate a generic HTTPError
    mock_client.request.side_effect = httpx.HTTPError("Generic Error")

    with pytest.raises(
        GraphQLClientException, match="HTTP request failed: Generic Error"
    ):
        await transport._http_request(mock_client, "POST", request, serializer)


@pytest.mark.asyncio
async def test_httpx_transport_status_error_handling() -> None:
    transport = HttpxTransport(endpoint="http://test.com")
    request = GraphQLRequest(query="{ test }")
    serializer = DefaultSerializer()

    mock_client = MagicMock(spec=httpx.AsyncClient)
    # Simulate an HTTPStatusError
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 400
    mock_response.content = b'{"errors": [{"message": "Bad Request"}]}'

    # In HttpxTransport._http_request, it checks status_code manually
    mock_client.request.return_value = mock_response

    with pytest.raises(GraphQLRequestException) as excinfo:
        await transport._http_request(mock_client, "POST", request, serializer)
    assert excinfo.value.response.json == {"errors": [{"message": "Bad Request"}]}


@pytest.mark.asyncio
async def test_httpx_transport_invalid_json_response() -> None:
    transport = HttpxTransport(endpoint="http://test.com")
    request = GraphQLRequest(query="{ test }")
    serializer = DefaultSerializer()

    mock_client = MagicMock(spec=httpx.AsyncClient)
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.content = b"invalid json"
    mock_client.request.return_value = mock_response

    resp = await transport._http_request(mock_client, "POST", request, serializer)
    assert resp.json is None


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
async def test_httpx_transport_coerce_value_async() -> None:
    transport = HttpxTransport(endpoint="http://test.com")
    serializer = DefaultSerializer()

    assert transport._coerce_value(True, serializer) == 1
    assert transport._coerce_value({"a": 1}, serializer) == '{"a":1}'


@pytest.mark.asyncio
async def test_httpx_transport_invalid_method_async() -> None:
    transport = HttpxTransport(endpoint="http://test")
    with pytest.raises(GraphQLClientException, match="Invalid method"):
        await transport.request(
            "INVALID", GraphQLRequest(query="{test}"), DefaultSerializer()
        )


@pytest.mark.asyncio
async def test_aiohttp_transport_invalid_method_async() -> None:
    transport = AiohttpTransport(endpoint="http://test")
    with pytest.raises(GraphQLClientException, match="Invalid method"):
        await transport.request(
            "INVALID", GraphQLRequest(query="{test}"), DefaultSerializer()
        )


@pytest.mark.asyncio
async def test_subscription_id_none_payload() -> None:
    req = GraphQLRequest(query="{ city { name } }")
    event = GraphQLSubscriptionEvent(
        request=req, json={"type": "data", "payload": {"data": {}}}
    )
    assert event.id is None
    assert event.type == GraphQLSubscriptionEventType.DATA
    assert cast("GraphQLResponse", event.payload).json == {"data": {}}


@pytest.mark.asyncio
async def test_subscription_connection_requests_minimal() -> None:
    sub = GraphQLSubscription(request="{ city { name } }")
    # request is string, so headers and payload logic changes
    init_req = sub.connection_init_request()
    assert init_req["type"] == "connection_init"
    assert init_req["payload"]["headers"] == {}

    start_req = sub.connection_start_request()
    assert start_req["type"] == "start"
    # When request is string, it's converted to GraphQLRequest, so it has payload
    assert start_req["payload"]["query"] == "{ city { name } }"


@pytest.mark.asyncio
async def test_subscription_handle_mismatch_id() -> None:
    mock_callbacks = MagicMock(spec=CallbackRegistry)
    req = GraphQLRequest(query="{ city { name } }")
    sub = GraphQLSubscription(request=req, callbacks=mock_callbacks)
    event = GraphQLSubscriptionEvent(
        request=req, json={"id": "other-id", "type": "data", "payload": {}}
    )
    await sub.handle(event)
    mock_callbacks.dispatch.assert_not_called()


@pytest.mark.asyncio
async def test_subscription_serializer_lazy_init() -> None:
    sub = GraphQLSubscription(request="{ city { name } }")
    object.__setattr__(sub, "serializer", None)

    mock_ws = MagicMock()

    async def mock_ws_aclose(*args: Any) -> None:
        pass

    mock_ws.__aexit__ = mock_ws_aclose

    async def mock_ws_aenter() -> Any:
        return mock_ws

    mock_ws.__aenter__ = mock_ws_aenter

    mock_transport = MagicMock()
    mock_transport.subscribe.return_value = mock_ws

    # This will trigger the lazy init of serializer in _websocket_connect
    # We need to mock more to make it not fail later, or just test the part
    import contextlib

    with contextlib.suppress(Exception):
        await sub._websocket_connect("http://test", mock_transport)

    assert sub.serializer is not None


def test_transport_base_abstracts() -> None:
    with pytest.raises(TypeError):
        GraphQLTransport()  # type: ignore[misc]
    with pytest.raises(TypeError):
        GraphQLSubscriptionTransport()  # type: ignore[misc]


def test_resolver_is_httpx_available_version_check() -> None:
    with patch("importlib.metadata.version", return_value="0.23.0"):
        assert _is_httpx_available(min_version="0.24.0") is False
    with patch("importlib.metadata.version", return_value="0.24.0"):
        assert _is_httpx_available(min_version="0.24.0") is True
    with patch(
        "importlib.metadata.version",
        side_effect=importlib.metadata.PackageNotFoundError,
    ):
        assert _is_httpx_available() is False


def test_resolver_explicit_transport_not_found() -> None:
    with (
        patch(
            "aiographql.client.transport.resolver._is_httpx_available",
            return_value=False,
        ),
        pytest.raises(ImportError, match="httpx is not installed"),
    ):
        get_default_transport("http://test", transport="httpx")

    with (
        patch(
            "aiographql.client.transport.resolver._is_aiohttp_available",
            return_value=False,
        ),
        pytest.raises(ImportError, match="aiohttp is not installed"),
    ):
        get_default_transport("http://test", transport="aiohttp")


def test_resolver_subscription_explicit_transport_not_found() -> None:
    with (
        patch(
            "aiographql.client.transport.resolver._is_aiohttp_available",
            return_value=False,
        ),
        pytest.raises(ImportError, match="aiohttp is not installed"),
    ):
        get_default_subscription_transport("http://test", transport="aiohttp")


def test_resolver_no_transport_available() -> None:
    with (
        patch(
            "aiographql.client.transport.resolver._is_aiohttp_available",
            return_value=False,
        ),
        patch(
            "aiographql.client.transport.resolver._is_httpx_available",
            return_value=False,
        ),
    ):
        with pytest.raises(RuntimeError, match="No suitable transport found"):
            get_default_transport("http://test")

        with pytest.raises(
            RuntimeError, match="No suitable subscription transport found"
        ):
            get_default_subscription_transport("http://test")
