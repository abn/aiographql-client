import asyncio
from typing import Any, AsyncGenerator, Dict, List

import pytest
from cafeteria.asyncio.callbacks import CallbackRegistry

from aiographql.client import (
    GraphQLClient,
    GraphQLClientValidationException,
    GraphQLRequest,
    GraphQLSubscription,
    GraphQLSubscriptionEvent,
    GraphQLSubscriptionEventType,
)

pytestmark = pytest.mark.asyncio


@pytest.fixture
async def client(server_apollo_v2: str) -> AsyncGenerator[GraphQLClient, None]:
    async with GraphQLClient(endpoint=server_apollo_v2) as client:
        yield client


@pytest.fixture
def query() -> str:
    return "query { ping }"


@pytest.fixture
def invalid_query_schema() -> str:
    return "query { pinged }"


@pytest.fixture
def query_output() -> Dict[str, str]:
    return {"ping": "pong"}


@pytest.fixture
def subscription_query() -> str:
    return "subscription { messageAdded }"


async def test_apollo_v2_simple_query(
    client: GraphQLClient, query: str, query_output: Dict[str, str]
) -> None:
    request = GraphQLRequest(query=query)
    response = await client.query(request)
    assert response.data == query_output


async def test_apollo_v2_invalid_query_schema(
    client: GraphQLClient, headers: Dict[str, str], invalid_query_schema: str
) -> None:
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


async def test_apollo_v2_subscription(
    client: GraphQLClient, subscription_query: str
) -> None:
    request = GraphQLRequest(query=subscription_query)
    m: List[Dict[str, Any]] = []

    def callback(data: Dict[str, Any]) -> None:
        assert "messageAdded" in data
        m.append(data)
        if len(m) > 1:
            message = data.get("messageAdded")
            assert message is not None
            assert len(message) > 0
            subscription.unsubscribe()

    callbacks = CallbackRegistry()
    callbacks.register(
        GraphQLSubscriptionEventType.DATA,
        lambda event: callback(event.payload.data),
    )

    # apollo-server v2 requires the sub-protocol to be configured
    subscription: GraphQLSubscription = await client.subscribe(
        request=request, callbacks=callbacks, protocols="graphql-ws"
    )

    await asyncio.sleep(0.1)

    try:
        if subscription.task is not None:
            await asyncio.wait_for(subscription.task, timeout=5)
        assert len(m) > 0
    except (asyncio.TimeoutError, asyncio.CancelledError):
        pytest.fail("Subscriptions timed out before receiving expected messages")
