"""
This script demonstrates how to use standard Python `dataclasses` with `aiographql-client`.
Scenario: Defining data structures using standard Python `dataclasses` and automatically parsing results into them.
"""

from __future__ import annotations

import asyncio
import logging

from dataclasses import dataclass

from aiographql.client import GraphQLClient


logger = logging.getLogger("dataclass_models")


# 1. Define standard Python dataclasses to ensure type safety and autocompletion
@dataclass
class City:
    name: str
    country: str
    population: int | None = None


@dataclass
class User:
    id: str
    username: str


async def main() -> None:
    # Initialize the client pointing to the Strawberry server
    logging.basicConfig(level=logging.INFO)
    async with GraphQLClient(endpoint="http://localhost:5000/graphql") as client:
        logger.info("--- Query: Get Cities as standard Python dataclasses ---")
        # Using 'query_data_as' for automatic parsing of results into models
        # It supports both standard Python dataclasses and Pydantic models (see data_models.py)
        cities: list[City] = await client.query_data_as(
            "{ cities { name country population } }", list[City], path="cities"
        )

        for city_item in cities:
            # Dataclasses provide IDE autocompletion and better structure
            logger.info(
                f"City: {city_item.name}, Country: {city_item.country}, "
                f"Population: {city_item.population}"
            )

        logger.info("--- Query: Get Specific City (London) as dataclass ---")
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
