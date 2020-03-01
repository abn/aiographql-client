from cafeteria.asyncio.callbacks import CallbackRegistry

from aiographql.client import (
    GraphQLRequest,
    GraphQLSubscription,
    GraphQLSubscriptionEventType,
)


def test_subscription_init_with_callback_default():
    subscription = GraphQLSubscription(request=GraphQLRequest(query="{}"))
    assert isinstance(subscription.callbacks, CallbackRegistry)
    assert not subscription.callbacks.callbacks()


def test_subscription_init_with_callback_none():
    subscription = GraphQLSubscription(
        request=GraphQLRequest(query="{}"), callbacks=None
    )
    assert isinstance(subscription.callbacks, CallbackRegistry)
    assert not subscription.callbacks.callbacks()


def test_subscription_init_with_callback_dict(mocker):
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
