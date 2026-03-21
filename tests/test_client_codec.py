from __future__ import annotations

import dataclasses
import uuid

from typing import Any

import pytest

from aiographql.client import GraphQLClient
from aiographql.client.codec import DefaultGraphQLCodec


@dataclasses.dataclass
class City:
    name: str


@pytest.mark.asyncio
async def test_client_query_data_as(mocker: Any) -> None:
    client = GraphQLClient(
        endpoint="http://test",
        codec=DefaultGraphQLCodec(),
        validate=False,
        transport="aiohttp",
    )

    mock_response_json = {"data": {"cities": [{"name": "London"}, {"name": "Paris"}]}}

    # Mocking _http_request to avoid actual network call
    mock_response = mocker.Mock()
    mock_response.json = mock_response_json
    mock_response.status = 200

    # We need to mock the session and the response from session.request
    mock_resp_ctx = mocker.AsyncMock()
    mock_resp_ctx.__aenter__.return_value = mocker.Mock()
    mock_resp_ctx.__aenter__.return_value.read = mocker.AsyncMock(
        return_value=b'{"data": {"cities": [{"name": "London"}, {"name": "Paris"}]}}'
    )
    mock_resp_ctx.__aenter__.return_value.status = 200

    mocker.patch("aiohttp.ClientSession.request", return_value=mock_resp_ctx)

    cities = await client.query_data_as(
        "{ cities { name } }", list[City], path="cities"
    )

    assert len(cities) == 2
    assert cities[0].name == "London"
    assert isinstance(cities[0], City)


@pytest.mark.asyncio
async def test_client_encode_variables(mocker: Any) -> None:
    codec = DefaultGraphQLCodec()
    client = GraphQLClient(
        endpoint="http://test",
        codec=codec,
        validate=False,
        transport="aiohttp",
    )

    @dataclasses.dataclass
    class CreateCityInput:
        name: str
        id: uuid.UUID

    city_id = uuid.uuid4()
    variables = {"input": CreateCityInput(name="Berlin", id=city_id)}

    mock_resp_ctx = mocker.AsyncMock()
    mock_resp_ctx.__aenter__.return_value = mocker.Mock()
    mock_resp_ctx.__aenter__.return_value.read = mocker.AsyncMock(
        return_value=b'{"data": {"createCity": {"name": "Berlin"}}}'
    )
    mock_resp_ctx.__aenter__.return_value.status = 200

    mock_request = mocker.patch(
        "aiohttp.ClientSession.request", return_value=mock_resp_ctx
    )

    await client.query(
        "mutation($input: CityInput) { createCity(input: $input) { name } }",
        variables=variables,
    )

    # Check that variables were encoded
    _args, kwargs = mock_request.call_args
    import orjson

    payload = orjson.loads(kwargs["data"])
    assert payload["variables"]["input"]["id"] == str(city_id)
    assert payload["variables"]["input"]["name"] == "Berlin"


@pytest.mark.asyncio
async def test_response_data_as() -> None:
    from aiographql.client.request import GraphQLRequest
    from aiographql.client.response import GraphQLResponse

    request = GraphQLRequest(query="{ test }", codec=DefaultGraphQLCodec())
    response = GraphQLResponse(request=request, json={"data": {"test": {"value": 42}}})

    @dataclasses.dataclass
    class TestData:
        value: int

    res = response.data_as(TestData, path="test")
    assert res.value == 42
    assert isinstance(res, TestData)
