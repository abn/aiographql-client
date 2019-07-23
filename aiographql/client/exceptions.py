import json
from typing import Optional

import graphql

from aiographql.client.transaction import GraphQLTransaction


class GraphQLClientException(Exception):
    pass


class GraphQLClientValidationException(GraphQLClientException):
    def __init__(self, *args: graphql.GraphQLError) -> None:
        message = "Query validation failed\n"
        for error in args:
            message += f"\n{str(error)}"
        super().__init__(message)


class GraphQLTransactionException(GraphQLClientException):
    def __init__(self, transaction: GraphQLTransaction) -> None:
        super().__init__(
            f"Transaction failed with response {json.dumps(transaction.response.json)}"
        )
        self.transaction = transaction


class GraphQLIntrospectionException(GraphQLClientException):
    def __init__(self, message: Optional[str] = None) -> None:
        super().__init__(message or "Something went wrong during introspection process")
