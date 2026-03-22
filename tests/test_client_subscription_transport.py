from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock
from unittest.mock import MagicMock

import pytest

from aiographql.client import GraphQLClient
from aiographql.client import GraphQLRequest
from aiographql.client.transport import GraphQLSubscriptionTransport


pytestmark = pytest.mark.asyncio


if TYPE_CHECKING:
    from pytest_mock import MockerFixture


async def test_client_init_subscription_transport(mocker: MockerFixture) -> None:
    mock_transport = MagicMock(spec=GraphQLSubscriptionTransport)
    # Mocking subscribe to avoid actual network calls
    mock_transport.subscribe = AsyncMock()

    client = GraphQLClient(
        endpoint="http://example.com/graphql",
        subscription_transport=mock_transport,
        validate=False,
    )

    # Check if the private attribute is set
    assert client._subscription_transport == mock_transport

    request = GraphQLRequest(query="subscription { test }")

    # We mock GraphQLSubscription to see if it receives the transport we provided to the client
    mock_subscription_class = mocker.patch(
        "aiographql.client.client.GraphQLSubscription"
    )
    mock_subscription_instance = mock_subscription_class.return_value
    mock_subscription_instance.subscribe = AsyncMock()

    await client.subscribe(request)
    # Check if GraphQLSubscription was called with our mock_transport
    _args, kwargs = mock_subscription_class.call_args
    assert kwargs["transport"] == mock_transport


async def test_client_subscribe_override_transport(mocker: MockerFixture) -> None:
    default_mock_transport = MagicMock(spec=GraphQLSubscriptionTransport)
    override_mock_transport = MagicMock(spec=GraphQLSubscriptionTransport)

    client = GraphQLClient(
        endpoint="http://example.com/graphql",
        subscription_transport=default_mock_transport,
        validate=False,
    )

    request = GraphQLRequest(query="subscription { test }")

    # We mock GraphQLSubscription to see if it receives the override transport
    mock_subscription_class = mocker.patch(
        "aiographql.client.client.GraphQLSubscription"
    )
    mock_subscription_instance = mock_subscription_class.return_value
    mock_subscription_instance.subscribe = AsyncMock()

    await client.subscribe(request, transport=override_mock_transport)
    # Check if GraphQLSubscription was called with override_mock_transport
    _args, kwargs = mock_subscription_class.call_args
    assert kwargs["transport"] == override_mock_transport
