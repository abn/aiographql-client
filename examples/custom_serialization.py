"""
This script demonstrates how to use a custom `GraphQLSerializer` and `GraphQLCodec`.
Scenario: Using a custom serializer that wraps JSON and a custom codec that handles `datetime` objects.
"""

from __future__ import annotations

import asyncio
import json
import logging

from datetime import datetime
from typing import Any

from aiographql.client import GraphQLClient
from aiographql.client.codec import DefaultGraphQLCodec


logger = logging.getLogger("custom_serialization")


# 1. Implement a custom serializer
class CustomJSONSerializer:
    """
    Custom serializer that adds extra indentation to outgoing JSON for demonstration.
    """

    def loads(self, data: str | bytes) -> Any:
        return json.loads(data)

    def dumps(self, value: Any) -> str | bytes:
        # Custom serialization logic (e.g., adding indentation)
        return json.dumps(value, indent=4)


async def main() -> None:
    # Initialize basic logging
    logging.basicConfig(level=logging.INFO)

    # 2. Configure a custom codec
    # The DefaultGraphQLCodec can be extended to handle custom types
    codec = DefaultGraphQLCodec()

    # Register a decoder for 'datetime' (assuming the server returns ISO strings)
    # The Strawberry server example doesn't have a datetime field by default,
    # but this shows how you would handle it if it did.
    def decode_datetime(value: str) -> datetime:
        return datetime.fromisoformat(value)

    codec.register_decoder(datetime, decode_datetime)

    # Initialize the client with the custom serializer and codec
    async with GraphQLClient(
        endpoint="http://localhost:5000/graphql",
        serializer=CustomJSONSerializer(),
        codec=codec,
    ) as client:
        logger.info("--- Query: Using Custom Serializer and Codec ---")

        # In a real scenario, if the server returned a 'createdAt' ISO string,
        # and we requested it as a datetime object, the codec would handle it:
        # created_at: datetime = await client.query_data_as(
        #     "{ city(name: \"London\") { createdAt } }", datetime, path="city.createdAt"
        # )

        response = await client.query("{ cities { name } }")
        if response.json and response.json.get("data"):
            cities = response.json["data"]["cities"]
            logger.info(f"Retrieved {len(cities)} cities using custom serializer.")

        # We can also see the codec in action by encoding variables
        variables = {"now": datetime.now()}
        # The default encoder would fail on datetime unless it's handled.
        # We can register an encoder too:
        codec.register_encoder(datetime, lambda dt: dt.isoformat())

        # When making a request with variables, the client uses the codec's encode method
        logger.info("--- Query: Using variables with custom codec ---")
        # To avoid validation errors, we must use the declared variable in the query
        response = await client.query(
            "query ($now: String) { cities { name } hello(extra: $now) }",
            variables=variables,
        )
        if response.json and response.json.get("data"):
            logger.info("Successfully sent request with datetime variable.")


if __name__ == "__main__":
    # Ensure the Strawberry server is running:
    # podman compose run --build strawberry-server
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"Error: {e}")
        logger.info("Make sure the Strawberry server is running.")
        logger.info("Run: podman compose run --build strawberry-server")
