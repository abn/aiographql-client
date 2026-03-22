"""
This script demonstrates how to use Pydantic models for type-safe GraphQL data handling.
Scenario: Defining models for a City and User, then automatically parsing responses into them.
"""

from __future__ import annotations

import asyncio
import logging

from pydantic import BaseModel

from aiographql.client import GraphQLClient


logger = logging.getLogger("data_models")


# 1. Define Pydantic models to ensure type safety and autocompletion
class City(BaseModel):
    name: str
    country: str
    population: int | None = None


class User(BaseModel):
    id: str
    username: str


async def main() -> None:
    # Initialize the client pointing to the Strawberry server
    # The strawberry server is configured to run on port 5000 in docker-compose.yaml
    logging.basicConfig(level=logging.INFO)
    async with GraphQLClient(endpoint="http://localhost:5000/graphql") as client:
        logger.info("--- Query: Get Cities as Pydantic models ---")
        # Using 'query_data_as' for automatic parsing of results into models
        cities: list[City] = await client.query_data_as(
            "{ cities { name country population } }", list[City], path="cities"
        )

        for city_item in cities:
            # Pydantic models provide IDE autocompletion and validation
            logger.info(
                f"City: {city_item.name}, Country: {city_item.country}, "
                f"Population: {city_item.population}"
            )

        logger.info("--- Query: Get Specific City (London) as model ---")
        # Extracting a single item by path
        city: City | None = await client.query_data_as(
            '{ city(name: "London") { name country population } }', City, path="city"
        )
        if city is not None:
            logger.info(
                f"City Found: {city.name}, Country: {city.country}, "
                f"Population: {city.population}"
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
