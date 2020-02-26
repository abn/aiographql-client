import os
import uuid

import pytest

from aiographql.client.client import GraphQLClient
from aiographql.client.request import GraphQLRequest


def pytest_addoption(parser):
    parser.addoption(
        "--world-server",
        action="store",
        default=os.environ.get(
            "WORLD_SERVER_GRAPHQL_ENDPOINT", "http://127.0.0.1:8080/v1/graphql"
        ),
        help="GraphQL server to use for integration tests",
    )


@pytest.fixture
def headers():
    return {"x-hasura-admin-secret": "secret"}


@pytest.fixture
def server(request):
    return request.config.getoption("--world-server")


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
def invalid_query():
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
