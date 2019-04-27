import pytest

from aiographql.client.client import GraphQLClient
from aiographql.client.transaction import GraphQLRequest

# noinspection SpellCheckingInspection
pytestmark = pytest.mark.asyncio


@pytest.fixture(autouse=True)
def client() -> GraphQLClient:
    return GraphQLClient(endpoint="https://graphql-pokemon.now.sh/")


async def test_simple_anonymous_query(client):
    request = GraphQLRequest(
        query="""
        {
            pokemon(name: "Pikachu") {
                id, name
            }
        }
        """
    )
    transaction = await client.post(request)

    assert transaction.response.data == {
        "pokemon": {"id": "UG9rZW1vbjowMjU=", "name": "Pikachu"}
    }
