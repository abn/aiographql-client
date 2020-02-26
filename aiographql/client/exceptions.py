from typing import Optional

import graphql
import ujson as json

from aiographql.client.response import GraphQLResponse


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
