from __future__ import annotations

from typing import TYPE_CHECKING

import orjson as json


if TYPE_CHECKING:
    import graphql

    from aiographql.client.response import GraphQLResponse


class GraphQLClientException(Exception):
    pass


class GraphQLClientValidationException(GraphQLClientException):
    def __init__(self, *args: graphql.GraphQLError) -> None:
        message = "Query validation failed\n"
        for error in args:
            message += f"\n{error!s}"
        super().__init__(message)


class GraphQLRequestException(GraphQLClientException):
    def __init__(self, response: GraphQLResponse) -> None:
        super().__init__(
            f"Request failed with response {json.dumps(response.json).decode('utf-8')}"
        )
        self.response = response


class GraphQLIntrospectionException(GraphQLClientException):
    def __init__(self, message: str | None = None) -> None:
        super().__init__(message or "Something went wrong during introspection process")
