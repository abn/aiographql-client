from __future__ import annotations

import pytest

from pydantic import BaseModel

from aiographql.client import GraphQLClient


class User(BaseModel):
    id: int
    name: str


class CreateUserInput(BaseModel):
    name: str


@pytest.mark.asyncio
async def test_client_pydantic_variables(mocker):
    # Mock aiohttp session to avoid actual network requests
    mock_session = mocker.Mock()
    mock_response = mocker.AsyncMock()
    # Use a non-AsyncMock for status if it's accessed as an attribute
    type(mock_response).status = mocker.PropertyMock(return_value=200)

    import json

    response_json = {"data": {"createUser": {"id": 1, "name": "Alice"}}}
    mock_response.read.return_value = json.dumps(response_json).encode("utf-8")

    # aiohttp context manager: async with session.request(...) as resp
    mock_context_manager = mocker.MagicMock()
    mock_context_manager.__aenter__ = mocker.AsyncMock(return_value=mock_response)
    mock_context_manager.__aexit__ = mocker.AsyncMock()
    mock_session.request.return_value = mock_context_manager

    client = GraphQLClient(
        endpoint="http://localhost/graphql", session=mock_session, validate=False
    )

    user_input = CreateUserInput(name="Alice")
    query = "mutation CreateUser($input: CreateUserInput) { createUser(input: $input) { id name } }"

    # Passing Pydantic model in variables
    response = await client.query(query, variables={"input": user_input})

    assert response.data["createUser"]["name"] == "Alice"

    # Check that variables were encoded correctly before being sent
    call_args = mock_session.request.call_args
    # payload is in 'data' as JSON bytes or string
    sent_data = json.loads(call_args.kwargs["data"])
    assert sent_data["variables"]["input"] == {"name": "Alice"}


@pytest.mark.asyncio
async def test_client_pydantic_decode(mocker):
    mock_session = mocker.Mock()
    mock_response = mocker.AsyncMock()
    type(mock_response).status = mocker.PropertyMock(return_value=200)

    import json

    response_json = {"data": {"user": {"id": 1, "name": "Alice"}}}
    mock_response.read.return_value = json.dumps(response_json).encode("utf-8")
    mock_context_manager = mocker.MagicMock()
    mock_context_manager.__aenter__ = mocker.AsyncMock(return_value=mock_response)
    mock_context_manager.__aexit__ = mocker.AsyncMock()
    mock_session.request.return_value = mock_context_manager

    client = GraphQLClient(
        endpoint="http://localhost/graphql", session=mock_session, validate=False
    )

    query = "{ user(id: 1) { id name } }"
    user = await client.query_data_as(query, User, path="user")

    assert isinstance(user, User)
    assert user.id == 1
    assert user.name == "Alice"
