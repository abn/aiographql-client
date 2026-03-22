"""
This script demonstrates how to use GraphQL subscriptions for real-time updates.
Scenario: Subscribing to a counter on the server and handling data via callbacks.
"""

from __future__ import annotations

import asyncio
import logging

from typing import Any

from aiographql.client import GraphQLClient
from aiographql.client import GraphQLRequest


logger = logging.getLogger("subscriptions")


async def main() -> None:
    # Initialize the client pointing to the Strawberry server
    # The strawberry server is configured to run on port 5000 in docker-compose.yaml
    logging.basicConfig(level=logging.INFO)
    async with GraphQLClient(endpoint="http://localhost:5000/graphql") as client:
        logger.info("--- Subscription: Counting to 5 ---")

        # Subscriptions allow for long-lived connections and real-time data
        # We use callbacks to handle incoming data or errors
        def on_data(event: Any) -> None:
            # Access the incoming subscription data via the payload
            # The payload is a GraphQLResponse object for DATA and ERROR events
            if event.payload and event.payload.data:
                count = event.payload.data["count"]
                logger.info(f"Subscription event: current count is {count}")

        def on_error(error: Any) -> None:
            logger.error(f"Subscription error: {error}")

        # Start the subscription
        # 'wait=True' means the call will block until the subscription completes
        await client.subscribe(
            GraphQLRequest(query="subscription { count(target: 5) }"),
            on_data=on_data,
            on_error=on_error,
            wait=True,
        )

        logger.info("Subscription completed successfully.")

        logger.info("--- Subscription: Real-time City notifications ---")

        # Example of another subscription
        def on_city_added(event: Any) -> None:
            if event.payload and event.payload.data:
                city = event.payload.data["city_added"]
                logger.info(
                    f"Notification: New city added - {city['name']} ({city['country']})"
                )

        await client.subscribe(
            GraphQLRequest(
                query="subscription { city_added { name country population } }"
            ),
            on_data=on_city_added,
            wait=True,
        )
        logger.info("Notification subscription completed.")


if __name__ == "__main__":
    # Ensure the Strawberry server is running:
    # podman compose run --build strawberry-server
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"Error: {e}")
        logger.info("Make sure the Strawberry server is running.")
        logger.info("Run: podman compose run --build strawberry-server")
