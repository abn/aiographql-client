from __future__ import annotations

import uuid

from typing import Any

import orjson
import pytest

from aiographql.client import GraphQLClient
from aiographql.client import GraphQLRequest


@pytest.mark.asyncio
async def test_custom_serializer_uuid() -> None:
    # Example from the issue: serialization of uuid.UUIDs
    user_id = uuid.uuid4()

    class CustomSerializer:
        def loads(self, data: str | bytes) -> Any:
            return orjson.loads(data)

        def dumps(self, obj: Any) -> str:
            return orjson.dumps(obj, option=orjson.OPT_INDENT_2).decode("utf-8")

    client = GraphQLClient(
        endpoint="http://localhost:8080/v1/graphql",
        serializer=CustomSerializer(),
        validate=False,
        transport="aiohttp",
    )

    request = client._prepare_request(
        request="query($id: uuid!) { user(id: $id) { name } }",
        variables={"id": user_id},
    )

    payload = request.payload()
    # variables should still contain the UUID object, as payload() doesn't serialize yet
    assert payload["variables"]["id"] == user_id

    # Verify the payload can be dumped with the serializer
    dumped_payload = client._serializer.dumps(payload)
    assert str(user_id) in dumped_payload


@pytest.mark.asyncio
async def test_custom_serializer_deserialization() -> None:
    # Custom load function that adds a prefix to keys (just for testing)
    class CustomSerializer:
        def loads(self, data: str | bytes) -> dict[str, Any]:
            obj = orjson.loads(data)
            return {"custom_" + k: v for k, v in obj.items()}

        def dumps(self, obj: Any) -> bytes:
            return orjson.dumps(obj)

    client = GraphQLClient(
        endpoint="http://localhost:8080/v1/graphql",
        serializer=CustomSerializer(),
        validate=False,
        transport="aiohttp",
    )

    # Mocking a response to test json_loads
    class MockResponse:
        status = 200

        async def read(self) -> bytes:
            return b'{"data": {"user": {"name": "John"}}}'

        async def __aenter__(self) -> MockResponse:
            return self

        async def __aexit__(self, *args: Any) -> None:
            pass

    from unittest.mock import MagicMock

    import aiohttp

    session = MagicMock(spec=aiohttp.ClientSession)
    session.request.return_value = MockResponse()

    response = await client.query(
        request=GraphQLRequest(query="{ user { name } }"),
        session=session,
        method="POST",
    )

    # Check if custom_loads was used
    assert "custom_data" in response.json
    assert response.json["custom_data"]["user"]["name"] == "John"
