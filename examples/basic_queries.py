"""
This script demonstrates basic GraphQL query operations using the aiographql-client.
Scenario: Retrieving a simple greeting and a list of cities from the server.
"""

from __future__ import annotations

import asyncio
import logging

from aiographql.client import GraphQLClient


logger = logging.getLogger("basic_queries")


async def main() -> None:
    # Initialize the client pointing to the Strawberry server
    # The strawberry server is configured to run on port 5000 in docker-compose.yaml
    logging.basicConfig(level=logging.INFO)
    async with GraphQLClient(endpoint="http://localhost:5000/graphql") as client:
        logger.info("--- Query: Basic Hello ---")
        # A simple string query
        response = await client.query("{ hello }")
        # Accessing data through the 'json' attribute of the response
        if response.json and response.json.get("data"):
            logger.info(f"Hello: {response.json['data']['hello']}")

        logger.info("--- Query: Get Cities ---")
        # Querying nested fields
        response = await client.query("{ cities { name country } }")
        if response.json and response.json.get("data"):
            cities = response.json["data"]["cities"]
            for city in cities:
                logger.info(f"City: {city['name']}, Country: {city['country']}")

        logger.info("--- Query: Get Specific City (London) ---")
        # Query with arguments
        response = await client.query(
            '{ city(name: "London") { name country population } }'
        )
        if response.json and response.json.get("data"):
            city = response.json["data"]["city"]
            if city:
                logger.info(
                    f"City Found: {city['name']}, Population: {city['population']}"
                )


if __name__ == "__main__":
    # Ensure the Strawberry server is running:
    # podman compose run --build strawberry-server
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"Error: {e}")
        logger.info("Make sure the Strawberry server is running.")
        logger.info("Run: podman compose run --build strawberry-server")
