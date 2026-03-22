"""
This script demonstrates how to perform authenticated GraphQL requests using custom headers.
Scenario: Providing a bearer token to fetch user profile information.
"""

from __future__ import annotations

import asyncio
import logging

from pydantic import BaseModel

from aiographql.client import GraphQLClient


# Define a model for the current user
logger = logging.getLogger("authenticated_requests")


class User(BaseModel):
    id: str
    username: str


async def main() -> None:
    # Initialize the client with authentication headers
    # The strawberry server checks for "Bearer secret-token"
    logging.basicConfig(level=logging.INFO)
    async with GraphQLClient(
        endpoint="http://localhost:5000/graphql",
        headers={"Authorization": "Bearer secret-token"},
    ) as client:
        logger.info("--- Query: Get Authenticated User ---")
        # This query requires the 'Authorization' header to succeed
        user: User | None = await client.query_data_as(
            "{ me { id username } }", User, path="me"
        )

        if user:
            logger.info(f"Logged in as: {user.username} (ID: {user.id})")
        else:
            logger.info("Authentication failed or user not found.")

        # You can also provide headers for a specific query
        logger.info("--- Query: Overriding headers for a specific call ---")
        response = await client.query(
            "{ me { username } }", headers={"Authorization": "Bearer invalid-token"}
        )
        if response.json and response.json.get("data"):
            logger.info(f"Result with invalid token: {response.json['data']['me']}")


if __name__ == "__main__":
    # Ensure the Strawberry server is running:
    # podman compose run --build strawberry-server
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"Error: {e}")
        logger.info("Make sure the Strawberry server is running.")
        logger.info("Run: podman compose run --build strawberry-server")
