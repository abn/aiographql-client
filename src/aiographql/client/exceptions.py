from __future__ import annotations

from typing import TYPE_CHECKING

import orjson as json


if TYPE_CHECKING:
    import graphql

    from aiographql.client.response import GraphQLResponse


class GraphQLClientException(Exception):
    pass


class GraphQLTransportException(GraphQLClientException):
    pass


class GraphQLClientValidationException(GraphQLClientException):
    def __init__(self, *args: graphql.GraphQLError) -> None:
        message = "Query validation failed\n"
        for error in args:
            message += f"\n{error!s}"
        super().__init__(message)


class GraphQLRequestException(GraphQLClientException):
    def __init__(self, response: GraphQLResponse) -> None:
        if response.errors:
            error_messages = [
                error.message for error in response.errors if error.message
            ]
            if error_messages:
                message = f"Request failed with errors: {', '.join(error_messages)}"
            else:
                message = "Request failed with unknown errors"
        else:
            message = "Request failed"
        super().__init__(message)
        self.response = response


class GraphQLIntrospectionException(GraphQLClientException):
    def __init__(self, message: str | None = None) -> None:
        super().__init__(message or "Something went wrong during introspection process")


class GraphQLCodecException(GraphQLClientException):
    pass
