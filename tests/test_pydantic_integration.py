from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Any

import pytest


if TYPE_CHECKING:
    from pydantic import BaseModel

from aiographql.client import GraphQLClient


pytestmark = [pytest.mark.pydantic, pytest.mark.asyncio]


def get_user_model() -> type[BaseModel]:
    from pydantic import BaseModel

    class User(BaseModel):
        id: int
        name: str

    return User


def get_input_model() -> type[BaseModel]:
    from pydantic import BaseModel

    class CreateUserInput(BaseModel):
        name: str

    return CreateUserInput


async def test_client_pydantic_variables(
    mocket: Any, httpretty: Any, strawberry_server: str
) -> None:
    create_user_input_model = get_input_model()

    endpoint = strawberry_server
    client = GraphQLClient(
        endpoint=endpoint,
        validate=False,
    )

    httpretty.register_uri(
        httpretty.POST,
        endpoint,
        body='{"data": {"createUser": {"id": 1, "name": "Alice"}}}',
        content_type="application/json",
    )

    user_input = create_user_input_model(name="Alice")
    query = "mutation CreateUser($input: CreateUserInput) { createUser(input: $input) { id name } }"

    # Passing Pydantic model in variables
    response = await client.query(query, variables={"input": user_input})

    assert response.data["createUser"]["name"] == "Alice"


async def test_client_pydantic_decode(
    mocket: Any, httpretty: Any, strawberry_server: str
) -> None:
    user_model = get_user_model()

    endpoint = strawberry_server
    client = GraphQLClient(
        endpoint=endpoint,
        validate=False,
    )

    httpretty.register_uri(
        httpretty.POST,
        endpoint,
        body='{"data": {"user": {"id": 1, "name": "Alice"}}}',
        content_type="application/json",
    )

    query = "{ user(id: 1) { id name } }"
    user = await client.query_data_as(query, user_model, path="user")

    assert isinstance(user, user_model)
    assert user.id == 1  # type: ignore[attr-defined]
    assert user.name == "Alice"  # type: ignore[attr-defined]
