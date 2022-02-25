import asyncio

import pytest
from cafeteria.asyncio.callbacks import CallbackRegistry

from aiographql.client import (
    GraphQLClient,
    GraphQLClientValidationException,
    GraphQLRequest,
    GraphQLSubscription,
    GraphQLSubscriptionEventType,
)

pytestmark = pytest.mark.asyncio


@pytest.fixture
def client(server_apollo_v2) -> GraphQLClient:
    return GraphQLClient(endpoint=server_apollo_v2)


@pytest.fixture
def query():
    return "query { ping }"


@pytest.fixture
def invalid_query_schema():
    return "query { pinged }"


@pytest.fixture
def query_output():
    return {"ping": "pong"}


@pytest.fixture
def subscription_query():
    return "subscription { messageAdded }"


async def test_apollo_v2_simple_query(client, query, query_output):
    request = GraphQLRequest(query=query)
    response = await client.query(request)
    assert response.data == query_output


async def test_apollo_v2_invalid_query_schema(client, headers, invalid_query_schema):
    request = GraphQLRequest(query=invalid_query_schema, headers=headers)
    with pytest.raises(GraphQLClientValidationException) as excinfo:
        _ = await client.query(request)
    message = str(excinfo.value)
    assert (
        """Query validation failed

Cannot query field 'pinged' on type 'Query'. Did you mean 'ping'?

GraphQL request:1:9
1 | query { pinged }
  |         ^"""
        == message
    )


async def test_apollo_v2_subscription(client, subscription_query):
    request = GraphQLRequest(query=subscription_query)
    m = []

    def callback(data):
        assert "messageAdded" in data
        m.append(data)
        if len(m) > 1:
            message = data.get("messageAdded")
            assert len(message) > 0
            subscription.unsubscribe()

    callbacks = CallbackRegistry()
    callbacks.register(
        GraphQLSubscriptionEventType.DATA, lambda event: callback(event.payload.data)
    )

    # apollo-server v2 requires the sub-protocol to be configured
    subscription: GraphQLSubscription = await client.subscribe(
        request=request, callbacks=callbacks, protocols="graphql-ws"
    )

    await asyncio.sleep(0.1)

    try:
        await asyncio.wait_for(subscription.task, timeout=5)
        assert len(m) > 0
    except asyncio.TimeoutError:
        pytest.fail("Subscriptions timed out before receiving expected messages")
