from __future__ import annotations

import dataclasses

from typing import Any

from aiographql.client.error import GraphQLError
from aiographql.client.request import GraphQLRequestContainer


@dataclasses.dataclass(frozen=True)
class GraphQLBaseResponse(GraphQLRequestContainer):
    json: dict[str, Any] = dataclasses.field(default_factory=dict)


@dataclasses.dataclass(frozen=True)
class GraphQLResponse(GraphQLBaseResponse):
    """
    GraphQL Response object wrapping response data and any errors. This object also
    contains the a copy of the :class:`GraphQLRequest` that produced this response.
    """

    @property
    def errors(self) -> list[GraphQLError]:
        """
        A list of :class:`GraphQLError` objects if server responded with query errors.
        """
        errors = self.json.get("errors")
        if errors is None:
            return []
        return [GraphQLError.load(error) for error in errors]

    @property
    def data(self) -> dict[str, Any]:
        """The data payload the server responded with."""
        data = self.json.get("data")
        return data if isinstance(data, dict) else {}

    @property
    def query(self) -> str:
        """The query string used to produce this response."""
        if isinstance(self.request, str):
            return self.request
        return self.request.query
