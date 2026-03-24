from __future__ import annotations

import asyncio

from typing import TYPE_CHECKING
from typing import Any

import graphql
import pytest

from cafeteria.asyncio.callbacks import CallbackRegistry
from graphql import GraphQLSyntaxError

from aiographql.client import GraphQLClient
from aiographql.client import GraphQLClientException
from aiographql.client import GraphQLClientValidationException
from aiographql.client import GraphQLIntrospectionException
from aiographql.client import GraphQLRequest
from aiographql.client import GraphQLRequestException
from aiographql.client import GraphQLSubscription
from aiographql.client import GraphQLSubscriptionEventType
from aiographql.client.response import GraphQLResponse


if TYPE_CHECKING:
    from pytest_mock import MockerFixture


pytestmark = pytest.mark.asyncio


async def test_introspect_success(
    mocker: MockerFixture, client: GraphQLClient, headers: dict[str, str]
) -> None:
    schema = graphql.build_schema("type Query { hello: String }")
    introspection_data = graphql.introspection_from_schema(schema, descriptions=False)

    mock_response = GraphQLResponse(
        request=mocker.Mock(), json={"data": introspection_data}
    )
    mocker.patch.object(
        client, "query", new_callable=mocker.AsyncMock, return_value=mock_response
    )

    result_schema = await client.introspect(headers=headers)

    assert isinstance(result_schema, graphql.GraphQLSchema)
    assert result_schema.query_type is not None
    assert result_schema.query_type.name == "Query"
    assert "hello" in result_schema.query_type.fields
    client.query.assert_called_once()  # type: ignore[attr-defined]


async def test_introspect_failure(
    mocker: MockerFixture, client: GraphQLClient, headers: dict[str, str]
) -> None:
    mock_response = GraphQLResponse(
        request=mocker.Mock(),
        json={"data": None, "errors": [{"message": "Some error"}]},
    )
    mocker.patch.object(
        client, "query", new_callable=mocker.AsyncMock, return_value=mock_response
    )

    with pytest.raises(GraphQLIntrospectionException) as excinfo:
        await client.introspect(headers=headers)

    assert "Failed to build schema from introspection data" in str(excinfo.value)
    client.query.assert_called_once()  # type: ignore[attr-defined]


async def test_simple_anonymous_post(
    client: GraphQLClient,
    headers: dict[str, str],
    query_city: str,
    query_output: dict[str, Any],
) -> None:
    request = GraphQLRequest(query=query_city, headers=headers)
    response = await client.post(request)
    assert response.data == query_output


async def test_simple_anonymous_post_with_string(
    client: GraphQLClient,
    headers: dict[str, str],
    query_city: str,
    query_output: dict[str, Any],
) -> None:
    response = await client.post(
        request=GraphQLRequest(query=query_city), headers=headers
    )
    assert response.data == query_output


async def test_simple_anonymous_query(
    client: GraphQLClient,
    headers: dict[str, str],
    query_city: str,
    query_output: dict[str, Any],
) -> None:
    request = GraphQLRequest(query=query_city, headers=headers)
    response = await client.query(request)
    assert response.data == query_output


async def test_invalid_query_schema(
    client: GraphQLClient, headers: dict[str, str], invalid_query_schema: str
) -> None:
    request = GraphQLRequest(query=invalid_query_schema, headers=headers)
    with pytest.raises(GraphQLClientValidationException) as excinfo:
        _ = await client.query(request)
    message = str(excinfo.value)
    assert (
        message
        == """Query validation failed

Cannot query field 'citeee' on type 'query_root'. Did you mean 'city'?

GraphQL request:3:11
2 |         query{
3 |           citeee {
  |           ^
4 |             id"""
    )


async def test_invalid_query_syntax(
    client: GraphQLClient, headers: dict[str, str], invalid_query_syntax: str
) -> None:
    request = GraphQLRequest(query=invalid_query_syntax, headers=headers)
    with pytest.raises(GraphQLSyntaxError):
        _ = await client.query(request)


async def test_invalid_method(
    client: GraphQLClient, headers: dict[str, str], query_city: str
) -> None:
    request = GraphQLRequest(query=query_city, headers=headers)
    with pytest.raises(GraphQLClientException):
        _ = await client.query(method="PUT", request=request)


async def test_unsuccessful_request(
    client: GraphQLClient,
    headers: dict[str, str],
    query_city: str,
    query_output: dict[str, Any],
) -> None:
    # hasura does not support GET requests, we use this to test this case
    request = GraphQLRequest(query=query_city, headers=headers)
    with pytest.raises(GraphQLRequestException) as excinfo:
        _ = await client.get(request)
    assert (
        'Request failed with response {"path":"$","error":"resource does not exist",'
        '"code":"not-found"}' in str(excinfo.value)
    )


async def test_external_aiohttp_session(
    mocker: MockerFixture,
    server: str,
    headers: dict[str, str],
    query_city: str,
    query_output: dict[str, Any],
) -> None:
    try:
        import aiohttp as _  # noqa: F401
    except ImportError:
        pytest.skip("aiohttp not installed")

    import aiohttp

    async with aiohttp.ClientSession() as session:
        client = GraphQLClient(endpoint=server, session=session)
        # Patching the ClientSession.request globally
        mock_request = mocker.patch(
            "aiohttp.ClientSession.request", wraps=session.request
        )
        response = await client.post(GraphQLRequest(query=query_city), headers=headers)
        assert response.data == query_output
        assert mock_request.called


async def test_mutation(
    client: GraphQLClient,
    headers: dict[str, str],
    mutation_city: str,
    mutation_output: dict[str, Any],
) -> None:
    request = GraphQLRequest(query=mutation_city, headers=headers)
    response = await client.query(request)
    assert response.data == mutation_output


async def test_subscription(
    client: GraphQLClient,
    headers: dict[str, str],
    subscription_query: str,
    mutation_city: str,
    city_name: str,
) -> None:
    request = GraphQLRequest(query=subscription_query, headers=headers)
    m: list[dict[str, Any]] = []

    def callback(data: dict[str, Any]) -> None:
        assert "city" in data
        m.append(data)
        if len(m) > 1:
            city_list = data.get("city")
            assert isinstance(city_list, list)
            city = city_list[0]
            assert city.get("name") == city_name
            subscription.unsubscribe()

    callbacks = CallbackRegistry()
    callbacks.register(
        GraphQLSubscriptionEventType.DATA,
        lambda event: callback(event.payload.data),
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
        if subscription.task is not None:
            await asyncio.wait_for(subscription.task, timeout=1)
        assert len(m) == 2
    except asyncio.TimeoutError:
        pytest.fail("Subscriptions timed out before receiving expected messages")


async def test_subscription_on_data_on_error_callbacks(
    client: GraphQLClient, subscription_query: str, headers: dict[str, str]
) -> None:
    request = GraphQLRequest(query=subscription_query, headers=headers)

    async def event_on_data(_: Any) -> None:
        pass

    def event_on_error(_: Any) -> None:
        pass

    subscription: GraphQLSubscription = await client.subscribe(
        request=request,
        headers=headers,
        on_data=event_on_data,
        on_error=event_on_error,
    )
    async with subscription:
        registry = subscription.callbacks
        assert isinstance(registry, CallbackRegistry)
        assert registry.exists(GraphQLSubscriptionEventType.DATA, event_on_data)
        assert registry.exists(GraphQLSubscriptionEventType.ERROR, event_on_error)


async def test_subscription_connection_init_payload(
    client: GraphQLClient, subscription_query: str, headers: dict[str, str]
) -> None:
    request = GraphQLRequest(query=subscription_query, headers=headers)
    connection_init_payload = {"authToken": "secret"}

    subscription: GraphQLSubscription = await client.subscribe(
        request=request,
        headers=headers,
        connection_init_payload=connection_init_payload,
    )
    async with subscription:
        assert subscription.connection_init_payload == connection_init_payload


async def test_get_schema_ttl(mocker: MockerFixture, client: GraphQLClient) -> None:
    client._schema_cache_ttl = 0.1
    mocker.patch.object(
        client, "introspect", new_callable=mocker.AsyncMock, return_value="mock_schema"
    )

    schema = await client.get_schema()
    assert schema == "mock_schema"
    client.introspect.assert_called_once()

    client.introspect.reset_mock()
    schema2 = await client.get_schema()
    assert schema2 == "mock_schema"
    client.introspect.assert_not_called()

    await asyncio.sleep(0.2)
    schema3 = await client.get_schema()
    assert schema3 == "mock_schema"
    client.introspect.assert_called_once()


async def test_query_method_session_override(mocker: MockerFixture) -> None:
    try:
        import aiohttp as _  # noqa: F401
    except ImportError:
        pytest.skip("aiohttp not installed")

    import aiohttp

    from aiographql.client.transport.aiohttp import AiohttpTransport

    endpoint = "http://example.com/graphql"
    # Disable validation to avoid introspection in this test
    client = GraphQLClient(endpoint=endpoint, validate=False)

    async with aiohttp.ClientSession() as custom_session:
        # We want to verify that custom_session is used
        if isinstance(client.transport, AiohttpTransport):
            mock_http_request = mocker.patch.object(
                client.transport, "_http_request", new_callable=mocker.AsyncMock
            )
            mock_http_request.return_value = mocker.MagicMock()

            await client.query("{ hello }", session=custom_session)

            mock_http_request.assert_called_once()
            args = mock_http_request.call_args[0]
            assert args[0] is custom_session
