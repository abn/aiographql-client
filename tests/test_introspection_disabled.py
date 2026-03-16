from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Any

import pytest

from aiographql.client import GraphQLClient
from aiographql.client import GraphQLIntrospectionException


if TYPE_CHECKING:
    from pytest_mock import MockerFixture


@pytest.mark.asyncio
async def test_query_with_introspection_disabled_global(
    mocker: MockerFixture,
    headers: dict[str, str],
    query_city: str,
    query_output: dict[str, Any],
) -> None:
    mocker.patch.object(
        GraphQLClient,
        "introspect",
        side_effect=GraphQLIntrospectionException("Introspection disabled"),
    )

    # By default, this should fail because it tries to validate
    async with GraphQLClient(endpoint="http://localhost:8080/v1/graphql") as client:
        with pytest.raises(GraphQLIntrospectionException):
            await client.query(query_city, headers=headers)

    # If we disable validation globally, it should succeed
    async with GraphQLClient(
        endpoint="http://localhost:8080/v1/graphql", validate=False
    ) as client_no_val:
        response = await client_no_val.query(query_city, headers=headers)
        assert response.data == query_output


@pytest.mark.asyncio
async def test_subscription_with_introspection_disabled_global(
    mocker: MockerFixture, headers: dict[str, str], subscription_query: str
) -> None:
    mocker.patch.object(
        GraphQLClient,
        "introspect",
        side_effect=GraphQLIntrospectionException("Introspection disabled"),
    )

    # Validation disabled globally
    async with GraphQLClient(
        endpoint="ws://localhost:8080/v1/graphql", validate=False
    ) as client:
        # Mocking subscription to not connect
        mocker.patch(
            "aiographql.client.subscription.GraphQLSubscription.subscribe",
            new_callable=mocker.AsyncMock,
        )

        from aiographql.client import GraphQLRequest

        subscription = await client.subscribe(
            GraphQLRequest(query=subscription_query), headers=headers
        )
        assert subscription is not None
