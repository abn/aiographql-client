from __future__ import annotations

import asyncio

from typing import TYPE_CHECKING

import strawberry

from strawberry.asgi import GraphQL
from strawberry.schema.config import StrawberryConfig
from strawberry.subscriptions import GRAPHQL_TRANSPORT_WS_PROTOCOL
from strawberry.subscriptions import GRAPHQL_WS_PROTOCOL


if TYPE_CHECKING:
    from collections.abc import AsyncGenerator


@strawberry.type
class City:
    name: str
    country: str


@strawberry.type
class Query:
    @strawberry.field
    def hello(self) -> str:
        return "world"

    @strawberry.field
    def city(self, name: str) -> City | None:
        if name == "London":
            return City(name="London", country="UK")
        return None

    @strawberry.field
    def cities(self) -> list[City]:
        return [
            City(name="London", country="UK"),
            City(name="Paris", country="France"),
        ]


@strawberry.type
class Mutation:
    @strawberry.mutation
    def add_city(self, name: str, country: str) -> City:
        return City(name=name, country=country)


@strawberry.type
class Subscription:
    @strawberry.subscription
    async def count(self, target: int = 5) -> AsyncGenerator[int, None]:
        for i in range(target):
            yield i
            await asyncio.sleep(0.1)

    @strawberry.subscription
    async def city_added(self) -> AsyncGenerator[City, None]:
        yield City(name="Berlin", country="Germany")
        await asyncio.sleep(0.1)
        yield City(name="Rome", country="Italy")


schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    subscription=Subscription,
    config=StrawberryConfig(auto_camel_case=False),
)

app = GraphQL(
    schema, subscription_protocols=[GRAPHQL_TRANSPORT_WS_PROTOCOL, GRAPHQL_WS_PROTOCOL]
)
