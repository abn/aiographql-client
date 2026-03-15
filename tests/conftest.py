import os
import uuid
from typing import Any, AsyncGenerator, Dict, Union

import pytest

from aiographql.client.client import GraphQLClient
from aiographql.client.request import GraphQLRequest


def pytest_addoption(parser: Any) -> None:
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
def headers() -> Dict[str, str]:
    return {"x-hasura-admin-secret": "secret"}


@pytest.fixture
def server(request: Any) -> str:
    val: str = request.config.getoption("--server-world-db")
    return val


@pytest.fixture
def server_apollo_v2(request: Any) -> str:
    val: str = request.config.getoption("--server-apollo-v2")
    return val


@pytest.fixture(autouse=True)
async def client(server: str) -> AsyncGenerator[GraphQLClient, None]:
    async with GraphQLClient(endpoint=server) as client:
        yield client


@pytest.fixture(scope="module")
def city_name() -> str:
    return str(uuid.uuid4())


@pytest.fixture
def subscription_query(city_name: str) -> str:
    return f"""
        subscription {{
          city(where: {{name: {{_eq: "{city_name}"}}}}) {{
            name
            id
          }}
        }}
    """  # noqa: B907


@pytest.fixture
def query_city() -> str:
    return """
        query{
          city(where: {name: {_eq: "Groningen"}}) {
            name
            id
          }
        }
        """


@pytest.fixture
def query_output() -> Dict[str, Any]:
    return {"city": [{"id": 11, "name": "Groningen"}]}


@pytest.fixture
def invalid_query_schema() -> str:
    return """
        query{
          citeee {
            id
          }
        }
        """


@pytest.fixture
def invalid_query_syntax() -> str:
    return """
        query{
          city(where: {name: {_eq: "Groningen"}}) {
            name
            id
        }
        """


@pytest.fixture
async def mutation_city(
    client: GraphQLClient, headers: Dict[str, str], city_name: str
) -> AsyncGenerator[str, None]:
    yield f"""
        mutation {{
          insert_city(objects: {{id: 4081, name: "{city_name}", population: 10, country_code: "GRC", district: "Greece"}}) {{
            affected_rows
          }}
        }}
    """  # noqa: B907
    delete_mutation = f"""
        mutation {{
          delete_city(where: {{name: {{_eq: "{city_name}"}}}}) {{
            affected_rows
          }}
        }}
        """  # noqa: B907
    request = GraphQLRequest(query=delete_mutation)
    _ = await client.query(request=request, headers=headers)


@pytest.fixture
def mutation_output() -> Dict[str, Any]:
    return {"insert_city": {"affected_rows": 1}}
