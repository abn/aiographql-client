import pytest
from typing import Dict, Any
from aiographql.client import GraphQLClient, GraphQLRequest, GraphQLIntrospectionException
from pytest_mock import MockerFixture

@pytest.mark.asyncio
async def test_query_with_introspection_disabled_global(mocker: MockerFixture, headers: Dict[str, str], query_city: str, query_output: Dict[str, Any]):
    mocker.patch.object(GraphQLClient, "introspect", side_effect=GraphQLIntrospectionException("Introspection disabled"))

    # By default, this should fail because it tries to validate
    client = GraphQLClient(endpoint="http://localhost:8080/v1/graphql")
    with pytest.raises(GraphQLIntrospectionException):
        await client.query(query_city, headers=headers)

    # If we disable validation globally, it should succeed
    client_no_val = GraphQLClient(endpoint="http://localhost:8080/v1/graphql", validate=False)

    response = await client_no_val.query(query_city, headers=headers)
    assert response.data == query_output

@pytest.mark.asyncio
async def test_subscription_with_introspection_disabled_global(mocker: MockerFixture, headers: Dict[str, str], subscription_query: str):
    mocker.patch.object(GraphQLClient, "introspect", side_effect=GraphQLIntrospectionException("Introspection disabled"))
    
    # Validation disabled globally
    client = GraphQLClient(endpoint="ws://localhost:8080/v1/graphql", validate=False)
    
    # Mocking subscription to not connect
    mocker.patch("aiographql.client.subscription.GraphQLSubscription.subscribe", new_callable=mocker.AsyncMock)
    
    subscription = await client.subscribe(subscription_query, headers=headers)
    assert subscription is not None
