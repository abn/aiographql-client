import asyncio

import pytest
from cafeteria.asyncio.callbacks import CallbackRegistry
from graphql import GraphQLSyntaxError
from aiohttp_socks import SocksVer

from aiographql.client.exceptions import GraphQLClientException
from aiographql.client.subscription import (
    GraphQLSubscription,
    GraphQLSubscriptionEventType,
)
from aiographql.client.client import GraphQLClient
from aiographql.client.transaction import GraphQLRequest

# noinspection SpellCheckingInspection
pytestmark = pytest.mark.asyncio


async def test_simple_anonymous_post(client, headers, query_city, query_output):
    request = GraphQLRequest(query=query_city, headers=headers)
    transaction = await client.post(request)
    assert transaction.response.data == query_output


async def test_simple_anonymous_query(client, headers, query_city, query_output):
    request = GraphQLRequest(query=query_city, headers=headers)
    transaction = await client.query(request)
    assert transaction.response.data == query_output

async def test_simple_anonymous_query_socks(headers, query_city, query_output):
    client = GraphQLClient(endpoint='http://127.0.0.1:8080/v1/graphql')
    request = GraphQLRequest(query=query_city, headers=headers,
        socks={'host': '127.0.0.1', 'port': 1080, 'rdns': False})
    transaction = await client.query(request)
    assert transaction.response.data == query_output


async def test_invalid_query(client, headers, invalid_query):
    request = GraphQLRequest(query=invalid_query, headers=headers)
    with pytest.raises(GraphQLSyntaxError):
        _ = await client.query(request)


async def test_invalid_method(client, headers, query_city):
    request = GraphQLRequest(query=query_city, headers=headers)
    with pytest.raises(GraphQLClientException):
        _ = await client.request(method="PUT", request=request)


async def test_mutation(client, headers, mutation_city, mutation_output):
    request = GraphQLRequest(query=mutation_city, headers=headers)
    transaction = await client.query(request)
    assert transaction.response.data == mutation_output


async def test_subscription(
    client, headers, subscription_query, mutation_city, city_name
):
    request = GraphQLRequest(query=subscription_query, headers=headers)
    callbacks = CallbackRegistry()
    m = []

    def callback(data):
        assert "city" in data.get("data")
        m.append(data)
        if len(m) > 1:
            city = data.get("data").get("city")[0]
            assert city.get("name") == city_name
            s1.cancel()

    callbacks.register(
        GraphQLSubscriptionEventType.DATA,
        lambda event: callback(event.message.payload.json),
    )

    subscription: GraphQLSubscription = await client.subscribe(
        request, callbacks, headers=headers
    )

    s1 = subscription.task
    asyncio.ensure_future(s1)

    await asyncio.sleep(0.1)

    request = GraphQLRequest(query=mutation_city, headers=headers)
    _ = await client.query(request)

    try:
        await asyncio.wait([s1], timeout=1)
        assert len(m) == 2
    except TimeoutError:
        pytest.fail("Subscriptions timed out before receiving expected messages")
