"""
This script demonstrates how to perform GraphQL mutations using variables.
Scenario: Adding a new city to the server using a parameterized mutation.
"""

from __future__ import annotations

import asyncio
import logging

from aiographql.client import GraphQLClient
from aiographql.client import GraphQLRequest


logger = logging.getLogger("mutations")


async def main() -> None:
    # Initialize the client pointing to the Strawberry server
    # The strawberry server is configured to run on port 5000 in docker-compose.yaml
    logging.basicConfig(level=logging.INFO)
    async with GraphQLClient(endpoint="http://localhost:5000/graphql") as client:
        logger.info("--- Mutation: Add City using variables ---")
        # Define the mutation with variables for clean, reusable code
        # This prevents injection attacks and improves readability
        request = GraphQLRequest(
            query="""
                mutation AddCity($name: String!, $country: String!, $population: Int) {
                    add_city(name: $name, country: $country, population: $population) {
                        name
                        country
                        population
                    }
                }
            """,
            variables={"name": "Tokyo", "country": "Japan", "population": 13960000},
        )

        # Use the 'post' method for mutations
        response = await client.post(request)
        if response.json and response.json.get("data"):
            new_city = response.json["data"]["add_city"]
            logger.info(
                f"Successfully added city: {new_city['name']} in {new_city['country']}"
            )
            logger.info(f"Population: {new_city['population']}")


if __name__ == "__main__":
    # Ensure the Strawberry server is running:
    # podman compose run --build strawberry-server
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"Error: {e}")
        logger.info("Make sure the Strawberry server is running.")
        logger.info("Run: podman compose run --build strawberry-server")
