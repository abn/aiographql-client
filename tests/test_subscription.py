from __future__ import annotations

from typing import TYPE_CHECKING

from cafeteria.asyncio.callbacks import CallbackRegistry

from aiographql.client import GraphQLRequest
from aiographql.client import GraphQLSubscription
from aiographql.client import GraphQLSubscriptionEventType


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
