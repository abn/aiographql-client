from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Any
from typing import cast
from unittest.mock import MagicMock

import pytest

from cafeteria.asyncio.callbacks import CallbackRegistry

from aiographql.client import GraphQLClient
from aiographql.client import GraphQLRequest
from aiographql.client import GraphQLResponse
from aiographql.client import GraphQLSubscription
from aiographql.client import GraphQLSubscriptionEventType
from aiographql.client.subscription import GraphQLSubscriptionEvent
from aiographql.client.transport.aiohttp import AiohttpSubscriptionTransport
from aiographql.client.transport.base import GraphQLSubscriptionTransport
from aiographql.client.transport.base import GraphQLTransport
from aiographql.client.transport.httpx import HttpxTransport


if TYPE_CHECKING:
    from pytest_mock import MockerFixture


def test_subscription_init_with_callback_default() -> None:
    subscription = GraphQLSubscription(request=GraphQLRequest(query="{}"))
    assert isinstance(subscription.callbacks, CallbackRegistry)
    assert not subscription.callbacks.callbacks()


def test_subscription_init_with_callback_none() -> None:
    subscription = GraphQLSubscription(
        request=GraphQLRequest(query="{}"), callbacks=None
    )
    assert isinstance(subscription.callbacks, CallbackRegistry)
    assert not subscription.callbacks.callbacks()


def test_subscription_init_with_callback_dict(mocker: MockerFixture) -> None:
    subscription = GraphQLSubscription(
        request=GraphQLRequest(query="{}"),
        callbacks={
            GraphQLSubscriptionEventType.KEEP_ALIVE: mocker.Mock(),
            GraphQLSubscriptionEventType.DATA: [mocker.Mock(), mocker.Mock()],
        },
    )
    registry = subscription.callbacks

    assert isinstance(registry, CallbackRegistry)
    assert len(registry.callbacks(GraphQLSubscriptionEventType.KEEP_ALIVE)) == 1
    assert len(registry.callbacks(GraphQLSubscriptionEventType.DATA)) == 2


def test_subscription_connection_init_request_default() -> None:
    subscription = GraphQLSubscription(
        request=GraphQLRequest(query="{}", headers={"X-Test": "value"})
    )
    init_request = subscription.connection_init_request()
    assert init_request == {
        "type": "connection_init",
        "payload": {"headers": {"X-Test": "value"}},
    }


def test_subscription_connection_init_request_extra_payload() -> None:
    subscription = GraphQLSubscription(
        request=GraphQLRequest(query="{}", headers={"X-Header": "v1"}),
        connection_init_payload={"authToken": "secret", "headers": {"X-Header": "v2"}},
    )
    init_request = subscription.connection_init_request()
    # Headers from request should win (v1)
    assert init_request == {
        "type": "connection_init",
        "payload": {"authToken": "secret", "headers": {"X-Header": "v1"}},
    }


def test_subscription_connection_init_request_no_mutation() -> None:
    extra_payload = {"authToken": "secret", "headers": {"X-Header": "v2"}}
    subscription = GraphQLSubscription(
        request=GraphQLRequest(query="{}", headers={"X-Header": "v1"}),
        connection_init_payload=extra_payload,
    )
    subscription.connection_init_request()
    assert extra_payload == {"authToken": "secret", "headers": {"X-Header": "v2"}}


def test_subscription_connection_init_request_empty_payload() -> None:
    subscription = GraphQLSubscription(
        request=GraphQLRequest(query="{}", headers={"X-Test": "value"}),
        connection_init_payload={},
    )
    init_request = subscription.connection_init_request()
    assert init_request["payload"] == {"headers": {"X-Test": "value"}}


def test_subscription_connection_init_request_non_dict_headers() -> None:
    subscription = GraphQLSubscription(
        request=GraphQLRequest(query="{}", headers={"X-Test": "value"}),
        connection_init_payload={"headers": "not-a-dict"},
    )
    init_request = subscription.connection_init_request()
    assert init_request["payload"] == {"headers": {"X-Test": "value"}}


def test_subscription_connection_init_request_string_request() -> None:
    # When request is a string, it is converted to GraphQLRequest in __post_init__
    # So we should test direct construction with a string if possible,
    # but GraphQLSubscription.request is typed as GraphQLRequest | str and
    # __post_init__ ensures it becomes GraphQLRequest.
    subscription = GraphQLSubscription(
        request="subscription { hello }",
        connection_init_payload={"authToken": "token"},
    )
    init_request = subscription.connection_init_request()
    assert init_request["payload"]["authToken"] == "token"
    # Default headers for a new GraphQLRequest is {}
    assert init_request["payload"]["headers"] == {}


async def test_subscription_context_manager(mocker: MockerFixture) -> None:
    mock_unsubscribe = mocker.patch(
        "aiographql.client.subscription.GraphQLSubscription.unsubscribe_and_wait",
        new_callable=mocker.AsyncMock,
    )
    subscription = GraphQLSubscription(request=GraphQLRequest(query="{}"))

    async with subscription as sub:
        assert sub is subscription
        mock_unsubscribe.assert_not_called()

    mock_unsubscribe.assert_awaited_once()


def test_transport_base_abstracts() -> None:
    with pytest.raises(TypeError):
        GraphQLTransport()  # type: ignore[misc]
    with pytest.raises(TypeError):
        GraphQLSubscriptionTransport()  # type: ignore[misc]


@pytest.mark.asyncio
async def test_subscription_id_none_payload() -> None:
    req = GraphQLRequest(query="{ city { name } }")
    event = GraphQLSubscriptionEvent(
        request=req, json={"type": "data", "payload": {"data": {}}}
    )
    assert event.id is None
    assert event.type == GraphQLSubscriptionEventType.DATA
    assert cast("GraphQLResponse", event.payload).json == {"data": {}}


@pytest.mark.strawberry
@pytest.mark.asyncio
async def test_subscription_integration_strawberry(
    strawberry_client: GraphQLClient,
) -> None:
    results = []

    async def on_data(event: GraphQLSubscriptionEvent) -> None:
        payload = event.payload
        if isinstance(payload, GraphQLResponse):
            results.append(payload.data["count"])

    await strawberry_client.subscribe(
        "subscription { count(target: 3) }",  # type: ignore[arg-type]
        on_data=on_data,
        wait=True,
        protocols=["graphql-ws"],
    )
    assert results == [0, 1, 2]


@pytest.mark.asyncio
async def test_subscription_handle_mismatch_id(ws_message_data: str) -> None:
    mock_callbacks = MagicMock(spec=CallbackRegistry)
    req = GraphQLRequest(query="{ city { name } }")
    sub = GraphQLSubscription(request=req, callbacks=mock_callbacks)
    event = GraphQLSubscriptionEvent(
        request=req, json={"id": "other-id", "type": "data", "payload": {"data": {}}}
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


@pytest.mark.httpx
@pytest.mark.asyncio
async def test_subscription_routing_httpx(mocker: MockerFixture) -> None:
    """
    Verify that when the HTTP transport is httpx, subscription logic does NOT receive the httpx.AsyncClient.
    Instead, it should receive None (causing a new internal aiohttp session to be created).
    """
    import httpx

    from aiographql.client.client import GraphQLClient

    endpoint = "http://example.com/graphql"
    async with httpx.AsyncClient() as httpx_client:
        client = GraphQLClient(endpoint=endpoint, session=httpx_client, validate=False)
        assert isinstance(client.transport, HttpxTransport)

        mock_get_sub = mocker.patch(
            "aiographql.client.client.get_default_subscription_transport"
        )
        mock_get_sub.return_value = mocker.MagicMock(spec=AiohttpSubscriptionTransport)

        # We don't need to actually call subscribe()'s internal logic, just check what's passed to get_default_subscription_transport
        import contextlib

        with contextlib.suppress(Exception):
            await client.subscribe(GraphQLRequest("{ notifications { id } }"))

        mock_get_sub.assert_called_once()
        _, kwargs = mock_get_sub.call_args
        assert kwargs["session"] is None
        assert kwargs["session"] is not httpx_client


@pytest.mark.aiohttp
@pytest.mark.asyncio
async def test_subscription_routing_aiohttp(mocker: MockerFixture) -> None:
    """
    Verify that when the HTTP transport is aiohttp, subscription logic receives the same aiohttp.ClientSession.
    """
    import aiohttp

    from aiographql.client.client import GraphQLClient

    endpoint = "http://example.com/graphql"
    async with aiohttp.ClientSession() as aiohttp_session:
        client = GraphQLClient(
            endpoint=endpoint, session=aiohttp_session, validate=False
        )
        from aiographql.client.transport.aiohttp import AiohttpTransport

        assert isinstance(client.transport, AiohttpTransport)

        mock_get_sub = mocker.patch(
            "aiographql.client.client.get_default_subscription_transport"
        )
        mock_get_sub.return_value = mocker.MagicMock(spec=AiohttpSubscriptionTransport)

        import contextlib

        with contextlib.suppress(Exception):
            await client.subscribe(GraphQLRequest("{ notifications { id } }"))

        mock_get_sub.assert_called_once()
        _, kwargs = mock_get_sub.call_args
        assert kwargs["session"] is aiohttp_session
