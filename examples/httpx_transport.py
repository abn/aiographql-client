"""
This script demonstrates how to use `httpx` transport with `aiographql-client`.
Scenario: Sharing an `httpx.AsyncClient` between multiple `GraphQLClient` instances or with other HTTP requests.
"""

from __future__ import annotations

import asyncio
import logging

import httpx

from aiographql.client import GraphQLClient
from aiographql.client.transport.httpx import HttpxTransport


logger = logging.getLogger("httpx_transport")


async def main() -> None:
    # Set up basic logging to see what's happening
    logging.basicConfig(level=logging.INFO)

    # 1. Using HttpxTransport with a shared httpx.AsyncClient
    # This is useful when you have an existing httpx client or need to reuse sessions
    async with httpx.AsyncClient() as session:
        # Create the transport with the shared session
        transport = HttpxTransport(
            endpoint="http://localhost:5000/graphql", client=session
        )

        # Initialize the GraphQL client with the custom transport
        client = GraphQLClient(
            endpoint="http://localhost:5000/graphql", transport=transport
        )

        logger.info("--- Query: Using shared HttpxTransport ---")
        response = await client.query("{ cities { name country } }")

        if response.json and response.json.get("data"):
            cities = response.json["data"]["cities"]
            logger.info(f"Retrieved {len(cities)} cities using Httpx.")
            for city in cities:
                logger.info(f"- {city['name']} ({city['country']})")

        # You can still use the same httpx session for regular HTTP requests
        resp = await session.get("http://localhost:5000/graphql")
        logger.info(f"Direct session GET status: {resp.status_code}")

    # 2. Simple HttpxTransport initialization (auto-manages its own session)
    # The client will create and close its own internal httpx.AsyncClient
    transport = HttpxTransport(endpoint="http://localhost:5000/graphql")
    async with GraphQLClient(
        endpoint="http://localhost:5000/graphql", transport=transport
    ) as client:
        logger.info("--- Query: Auto-managed HttpxTransport ---")
        response = await client.query('{ city(name: "London") { name population } }')
        if response.json and response.json.get("data"):
            city = response.json["data"]["city"]
            logger.info(f"London population: {city['population']}")


if __name__ == "__main__":
    # Ensure the Strawberry server is running:
    # podman compose run --build strawberry-server
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"Error: {e}")
        logger.info("Make sure the Strawberry server is running.")
        logger.info("Run: podman compose run --build strawberry-server")
