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
