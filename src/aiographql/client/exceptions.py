from __future__ import annotations

from typing import TYPE_CHECKING, Optional

import graphql
import ujson as json

if TYPE_CHECKING:
    from aiographql.client import GraphQLResponse


class GraphQLClientException(Exception):
    pass


class GraphQLClientValidationException(GraphQLClientException):
    def __init__(self, *args: graphql.GraphQLError) -> None:
        message = "Query validation failed\n"
        for error in args:
            message += f"\n{str(error)}"
        super().__init__(message)


class GraphQLRequestException(GraphQLClientException):
    def __init__(self, response: GraphQLResponse) -> None:
        super().__init__(f"Request failed with response {json.dumps(response.json)}")
        self.response = response


class GraphQLIntrospectionException(GraphQLClientException):
    def __init__(self, message: Optional[str] = None) -> None:
        super().__init__(message or "Something went wrong during introspection process")
