import os
import uuid

import pytest

from aiographql.client.client import GraphQLClient
from aiographql.client.request import GraphQLRequest


def pytest_addoption(parser):
    parser.addoption(
        "--server-world-db",
        action="store",
        default=os.environ.get(
            "GRAPHQL_ENDPOINT_WORLD_SERVER", "http://127.0.0.1:8080/v1/graphql"
        ),
        help="GraphQL server to use for integration tests",
    )
    parser.addoption(
        "--server-apollo-v2",
        action="store",
        default=os.environ.get(
            "GRAPHQL_ENDPOINT_APOLLO_V2", "http://127.0.0.1:4000/graphql"
        ),
        help="GraphQL Apollo Server (v2) to use for integration tests",
    )


@pytest.fixture
def headers():
    return {"x-hasura-admin-secret": "secret"}


@pytest.fixture
def server(request):
    return request.config.getoption("--server-world-db")


@pytest.fixture
def server_apollo_v2(request):
    return request.config.getoption("--server-apollo-v2")


@pytest.fixture(autouse=True)
def client(server) -> GraphQLClient:
    return GraphQLClient(endpoint=server)


@pytest.fixture(scope="module")
def city_name():
    return str(uuid.uuid4())


@pytest.fixture
def subscription_query(city_name):
    return f"""
        subscription {{
          city(where: {{name: {{_eq: "{city_name}"}}}}) {{
            name
            id
          }}
        }}
    """


@pytest.fixture
def query_city():
    return """
        query{
          city(where: {name: {_eq: "Groningen"}}) {
            name
            id
          }
        }
        """


@pytest.fixture
def query_output():
    return {"city": [{"id": 11, "name": "Groningen"}]}


@pytest.fixture
def invalid_query_schema():
    return """
        query{
          citeee {
            id
          }
        }
        """


@pytest.fixture
def invalid_query_syntax():
    return """
        query{
          city(where: {name: {_eq: "Groningen"}}) {
            name
            id
        }
        """


@pytest.fixture
async def mutation_city(client, headers, city_name):
    yield f"""
        mutation {{
          insert_city(objects: {{id: 4081, name: "{city_name}", population: 10, country_code: "GRC", district: "Greece"}}) {{
            affected_rows
          }}
        }}
    """
    delete_mutation = f"""
        mutation {{
          delete_city(where: {{name: {{_eq: "{city_name}"}}}}) {{
            affected_rows
          }}
        }}
        """
    request = GraphQLRequest(query=delete_mutation)
    _ = await client.query(request=request, headers=headers)


@pytest.fixture
def mutation_output():
    return {"insert_city": {"affected_rows": 1}}
