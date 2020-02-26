import pytest

from aiographql.client import (
    GraphQLClient,
    GraphQLIntrospectionException,
    GraphQLRequest,
    GraphQLResponse,
)

pytestmark = pytest.mark.asyncio


@pytest.fixture
def server(request):
    return request.config.getoption("--world-server")


@pytest.fixture(autouse=True)
def client(server) -> GraphQLClient:
    return GraphQLClient(endpoint=server)


@pytest.fixture
def post():
    async def post(client, graphql_request):
        response = await client.post(request=graphql_request)
        return response

    yield post


@pytest.mark.asyncio
async def test_client_headers(server, headers, post, query_city):
    client = GraphQLClient(endpoint=server, headers=headers)
    graphql_request = GraphQLRequest(query=query_city)
    response = await post(client, graphql_request)
    assert isinstance(response, GraphQLResponse)


@pytest.mark.asyncio
async def test_request_headers(server, headers, post, query_city):
    client = GraphQLClient(endpoint=server)
    graphql_request = GraphQLRequest(query=query_city, headers=headers)
    response = await post(client, graphql_request)
    assert isinstance(response, GraphQLResponse)


@pytest.mark.asyncio
async def test_post_headers(server, headers, client, query_city):
    graphql_request = GraphQLRequest(query=query_city)
    response = await client.post(graphql_request, headers=headers)
    assert isinstance(response, GraphQLResponse)
    assert response.data
    assert not response.errors


@pytest.mark.asyncio
async def test_no_headers(server, client, query_city):
    graphql_request = GraphQLRequest(query=query_city)
    with pytest.raises(GraphQLIntrospectionException):
        response = await client.post(graphql_request)
        assert isinstance(response, GraphQLResponse)
        assert not response.data
        assert response.errors
