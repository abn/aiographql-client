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
    population: int | None = None


@strawberry.type
class User:
    id: str
    username: str


@strawberry.type
class Query:
    @strawberry.field
    def hello(self, extra: str | None = None) -> str:
        return "world"

    @strawberry.field
    def city(self, name: str) -> City | None:
        if name == "London":
            return City(name="London", country="UK", population=8908081)
        return None

    @strawberry.field
    def cities(self) -> list[City]:
        return [
            City(name="London", country="UK", population=8908081),
            City(name="Paris", country="France", population=2148271),
        ]

    @strawberry.field
    def me(self, info: strawberry.Info) -> User | None:
        # Simple authentication simulation via header
        auth_header = info.context.get("request").headers.get("Authorization")
        if auth_header == "Bearer secret-token":
            return User(id="1", username="admin")
        return None


@strawberry.type
class Mutation:
    @strawberry.mutation
    def add_city(self, name: str, country: str, population: int | None = None) -> City:
        return City(name=name, country=country, population=population)


@strawberry.type
class Subscription:
    @strawberry.subscription
    async def count(self, target: int = 5) -> AsyncGenerator[int, None]:
        for i in range(target):
            yield i
            await asyncio.sleep(0.1)

    @strawberry.subscription
    async def city_added(self) -> AsyncGenerator[City, None]:
        yield City(name="Berlin", country="Germany", population=3769495)
        await asyncio.sleep(0.1)
        yield City(name="Rome", country="Italy", population=2872800)


schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    subscription=Subscription,
    config=StrawberryConfig(auto_camel_case=False),
)


class MyGraphQL(GraphQL):
    async def get_context(
        self,
        request: strawberry.http.HTTPRequest | strawberry.http.WebSocketRequest,
        response: strawberry.http.HTTPResponse | None = None,
    ) -> dict:
        return {"request": request}


app = MyGraphQL(
    schema, subscription_protocols=[GRAPHQL_TRANSPORT_WS_PROTOCOL, GRAPHQL_WS_PROTOCOL]
)
