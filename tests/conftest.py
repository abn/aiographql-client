from __future__ import annotations

import importlib.util
import os
import uuid

from typing import TYPE_CHECKING
from typing import Any

import pytest

from mocket.mocket import Mocket
from mocket.plugins.httpretty import HTTPretty

from aiographql.client.client import GraphQLClient
from aiographql.client.request import GraphQLRequest


if TYPE_CHECKING:
    from collections.abc import AsyncGenerator


def _has_package(package_name: str) -> bool:
    return importlib.util.find_spec(package_name) is not None


HAS_AIOHTTP = _has_package("aiohttp")
HAS_HTTPX = _has_package("httpx")
HAS_WEBSOCKETS = _has_package("websockets")
HAS_PYDANTIC = _has_package("pydantic")


@pytest.fixture(autouse=True)
def _check_transport_availability(request: pytest.FixtureRequest) -> None:
    if request.node.get_closest_marker("aiohttp") and not HAS_AIOHTTP:
        pytest.skip("aiohttp not installed")
    if request.node.get_closest_marker("httpx") and not HAS_HTTPX:
        pytest.skip("httpx not installed")
    if request.node.get_closest_marker("websockets") and not HAS_WEBSOCKETS:
        pytest.skip("websockets not installed")
    if request.node.get_closest_marker("pydantic") and not HAS_PYDANTIC:
        pytest.skip("pydantic not installed")

    if request.node.get_closest_marker("strawberry"):
        import urllib.request

        strawberry_server_url = request.config.getoption("--server-strawberry")
        try:
            with urllib.request.urlopen(strawberry_server_url, timeout=1):
                pass
        except Exception as e:
            # Handle cases like 405 Method Not Allowed or 400 Bad Request which mean the server IS there
            # but doesn't like our empty/GET request.
            if hasattr(e, "code") and e.code in {400, 405}:
                pass
            else:
                pytest.skip(
                    f"strawberry server not available at {strawberry_server_url}: {e}"
                )


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line("markers", "aiohttp: mark test as requiring aiohttp")
    config.addinivalue_line("markers", "httpx: mark test as requiring httpx")
    config.addinivalue_line("markers", "websockets: mark test as requiring websockets")
    config.addinivalue_line("markers", "pydantic: mark test as requiring pydantic")
    config.addinivalue_line("markers", "strawberry: mark test as requiring strawberry")


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
    parser.addoption(
        "--server-strawberry",
        action="store",
        default=os.environ.get(
            "GRAPHQL_ENDPOINT_STRAWBERRY", "http://127.0.0.1:5000/graphql"
        ),
        help="GraphQL Strawberry Server to use for integration tests",
    )


@pytest.fixture
def headers() -> dict[str, str]:
    return {"x-hasura-admin-secret": "secret"}


@pytest.fixture
def server(request: Any) -> str:
    val: str = request.config.getoption("--server-world-db")
    return val


@pytest.fixture
def server_apollo_v2(request: Any) -> str:
    val: str = request.config.getoption("--server-apollo-v2")
    return val


@pytest.fixture
def strawberry_server(request: Any) -> str:
    val: str = request.config.getoption("--server-strawberry")
    return val


@pytest.fixture
def mocket() -> Any:
    Mocket.enable()
    yield Mocket
    Mocket.disable()


@pytest.fixture
def httpretty() -> Any:
    yield HTTPretty


@pytest.fixture
async def strawberry_client(
    strawberry_server: str,
) -> AsyncGenerator[GraphQLClient, None]:
    # Use ws:// for subscriptions if necessary, but GraphQLClient handles it
    endpoint = strawberry_server
    async with GraphQLClient(endpoint=endpoint) as client:
        yield client


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
    """


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
def query_output() -> dict[str, Any]:
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
    client: GraphQLClient, headers: dict[str, str], city_name: str
) -> AsyncGenerator[str, None]:
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
def mutation_output() -> dict[str, Any]:
    return {"insert_city": {"affected_rows": 1}}


@pytest.fixture
def ws_message_ka() -> str:
    return '{"type":"ka"}'


@pytest.fixture
def ws_message_connection_ack() -> str:
    return '{"type":"connection_ack"}'


@pytest.fixture
def ws_message_data() -> str:
    return (
        '{"type":"data","id":"1","payload":{"data":{"city":[{"id":1,"name":"Kabul"}]}}}'
    )


@pytest.fixture
def ws_message_error() -> str:
    return '{"type":"error","id":"1","payload":{"message":"an error occurred"}}'


@pytest.fixture
def ws_message_complete() -> str:
    return '{"type":"complete","id":"1"}'


@pytest.fixture
def ws_message_invalid_json() -> str:
    return '{"type":"data", "id": "1", "payload": {"data": {"city": '


@pytest.fixture
def ws_message_no_type() -> str:
    return '{"id":"1","payload":{"data":{"city":[{"id":1,"name":"Kabul"}]}}}'


@pytest.fixture
def ws_message_bad_payload() -> str:
    return '{"type":"data","id":"1","payload":"not a dict"}'
