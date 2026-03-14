import asyncio

import pytest
from cafeteria.asyncio.callbacks import CallbackRegistry
from graphql import GraphQLSyntaxError

import graphql
from aiographql.client import (
    GraphQLClientException,
    GraphQLClientValidationException,
    GraphQLIntrospectionException,
    GraphQLRequest,
    GraphQLRequestException,
    GraphQLSubscription,
    GraphQLSubscriptionEventType,
)
from aiographql.client.response import GraphQLResponse
from aiographql.client.helpers import aiohttp_client_session

pytestmark = pytest.mark.asyncio


async def test_introspect_success(mocker, client, headers):
    schema = graphql.build_schema("type Query { hello: String }")
    introspection_data = graphql.introspection_from_schema(schema, descriptions=False)

    mock_response = GraphQLResponse(
        request=mocker.Mock(), json={"data": introspection_data}
    )
    mocker.patch.object(client, "query", return_value=mock_response)

    result_schema = await client.introspect(headers=headers)

    assert isinstance(result_schema, graphql.GraphQLSchema)
    assert result_schema.query_type.name == "Query"
    assert "hello" in result_schema.query_type.fields
    client.query.assert_called_once()


async def test_introspect_failure(mocker, client, headers):
    mock_response = GraphQLResponse(
        request=mocker.Mock(),
        json={"data": None, "errors": [{"message": "Some error"}]},
    )
    mocker.patch.object(client, "query", return_value=mock_response)

    with pytest.raises(GraphQLIntrospectionException) as excinfo:
        await client.introspect(headers=headers)

    assert "Failed to build schema from introspection data" in str(excinfo.value)
    client.query.assert_called_once()


async def test_simple_anonymous_post(client, headers, query_city, query_output):
    request = GraphQLRequest(query=query_city, headers=headers)
    response = await client.post(request)
    assert response.data == query_output


async def test_simple_anonymous_post_with_string(
    client, headers, query_city, query_output
):
    response = await client.post(request=query_city, headers=headers)
    assert response.data == query_output


async def test_simple_anonymous_query(client, headers, query_city, query_output):
    request = GraphQLRequest(query=query_city, headers=headers)
    response = await client.query(request)
    assert response.data == query_output


async def test_invalid_query_schema(client, headers, invalid_query_schema):
    request = GraphQLRequest(query=invalid_query_schema, headers=headers)
    with pytest.raises(GraphQLClientValidationException) as excinfo:
        _ = await client.query(request)
    message = str(excinfo.value)
    assert (
        """Query validation failed

Cannot query field 'citeee' on type 'query_root'. Did you mean 'city'?

GraphQL request:3:11
2 |         query{
3 |           citeee {
  |           ^
4 |             id"""
        == message
    )


async def test_invalid_query_syntax(client, headers, invalid_query_syntax):
    request = GraphQLRequest(query=invalid_query_syntax, headers=headers)
    with pytest.raises(GraphQLSyntaxError):
        _ = await client.query(request)


async def test_invalid_method(client, headers, query_city):
    request = GraphQLRequest(query=query_city, headers=headers)
    with pytest.raises(GraphQLClientException):
        _ = await client.query(method="PUT", request=request)


async def test_unsuccessful_request(client, headers, query_city, query_output):
    # hasura does not support GET requests, we use this to test this case
    request = GraphQLRequest(query=query_city, headers=headers)
    with pytest.raises(GraphQLRequestException) as excinfo:
        _ = await client.get(request)
    assert (
        'Request failed with response {"path":"$","error":"resource does not exist",'
        '"code":"not-found"}' in str(excinfo.value)
    )


async def test_external_aiohttp_session(
    mocker, client, headers, query_city, query_output
):
    async with aiohttp_client_session() as session:
        spy = mocker.spy(session, "request")
        response = await client.post(query_city, headers=headers, session=session)
        assert response.data == query_output
        spy.assert_called_once()


async def test_mutation(client, headers, mutation_city, mutation_output):
    request = GraphQLRequest(query=mutation_city, headers=headers)
    response = await client.query(request)
    assert response.data == mutation_output


async def test_subscription(
    client, headers, subscription_query, mutation_city, city_name
):
    request = GraphQLRequest(query=subscription_query, headers=headers)
    m = []

    def callback(data):
        assert "city" in data
        m.append(data)
        if len(m) > 1:
            city = data.get("city")[0]
            assert city.get("name") == city_name
            subscription.unsubscribe()

    callbacks = CallbackRegistry()
    callbacks.register(
        GraphQLSubscriptionEventType.DATA, lambda event: callback(event.payload.data)
    )

    subscription: GraphQLSubscription = await client.subscribe(
        request=request,
        callbacks=callbacks,
        headers=headers,
    )

    await asyncio.sleep(0.1)

    request = GraphQLRequest(query=mutation_city, headers=headers)
    _ = await client.query(request)

    try:
        await asyncio.wait_for(subscription.task, timeout=1)
        assert len(m) == 2
    except asyncio.TimeoutError:
        pytest.fail("Subscriptions timed out before receiving expected messages")


async def test_subscription_on_data_on_error_callbacks(
    client, subscription_query, headers
):
    request = GraphQLRequest(query=subscription_query, headers=headers)

    async def event_on_data(_):
        pass

    def event_on_error(_):
        pass

    subscription: GraphQLSubscription = await client.subscribe(
        request=request,
        headers=headers,
        on_data=event_on_data,
        on_error=event_on_error,
    )
    registry = subscription.callbacks
    assert registry.exists(GraphQLSubscriptionEventType.DATA, event_on_data)
    assert registry.exists(GraphQLSubscriptionEventType.ERROR, event_on_error)
    await subscription.unsubscribe_and_wait()
