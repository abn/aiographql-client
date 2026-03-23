from __future__ import annotations

import asyncio

from typing import TYPE_CHECKING
from typing import Any

import pytest

from cafeteria.asyncio.callbacks import CallbackRegistry

from aiographql.client import GraphQLClient
from aiographql.client import GraphQLClientValidationException
from aiographql.client import GraphQLRequest
from aiographql.client import GraphQLSubscription
from aiographql.client import GraphQLSubscriptionEventType


if TYPE_CHECKING:
    from collections.abc import AsyncGenerator


pytestmark = pytest.mark.asyncio


@pytest.fixture(params=["v2"])
async def apollo_client_with_version(
    request: Any,
) -> AsyncGenerator[tuple[GraphQLClient, str], None]:
    version = request.param
    endpoint = request.config.getoption(f"--server-apollo-{version}")
    async with GraphQLClient(endpoint=endpoint) as client:
        yield client, version


@pytest.fixture
def query() -> str:
    return "query { ping }"


@pytest.fixture
def invalid_query_schema() -> str:
    return "query { pinged }"


@pytest.fixture
def query_output() -> dict[str, str]:
    return {"ping": "pong"}


@pytest.fixture
def subscription_query() -> str:
    return "subscription { messageAdded }"


async def test_apollo_simple_query(
    apollo_client_with_version: tuple[GraphQLClient, str],
    query: str,
    query_output: dict[str, str],
) -> None:
    client, _ = apollo_client_with_version
    request = GraphQLRequest(query=query)
    response = await client.query(request)
    assert response.data == query_output


async def test_apollo_invalid_query_schema(
    apollo_client_with_version: tuple[GraphQLClient, str],
    headers: dict[str, str],
    invalid_query_schema: str,
) -> None:
    client, _ = apollo_client_with_version
    request = GraphQLRequest(query=invalid_query_schema, headers=headers)
    with pytest.raises(GraphQLClientValidationException) as excinfo:
        _ = await client.query(request)
    message = str(excinfo.value)
    assert "Cannot query field 'pinged' on type 'Query'" in message


@pytest.mark.aiohttp
async def test_apollo_subscription(
    apollo_client_with_version: tuple[GraphQLClient, str], subscription_query: str
) -> None:
    client, version = apollo_client_with_version
    request = GraphQLRequest(query=subscription_query)
    m: list[dict[str, Any]] = []

    def callback(data: dict[str, Any]) -> None:
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

    subscription_kwargs: dict[str, Any] = {
        "request": request,
        "callbacks": callbacks,
    }

    # apollo-graphql_server v2 requires the sub-protocol to be configured
    subscription_kwargs["protocols"] = "graphql-ws"

    subscription: GraphQLSubscription = await client.subscribe(**subscription_kwargs)

    await asyncio.sleep(0.1)

    try:
        if subscription.task is not None:
            await asyncio.wait_for(subscription.task, timeout=10)
        assert len(m) > 0
    except (asyncio.TimeoutError, asyncio.CancelledError):
        pytest.fail(f"Subscriptions timed out for Apollo {version}")
