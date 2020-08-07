from dataclasses import dataclass, field
from typing import Any, Dict, List

from aiographql.client.error import GraphQLError
from aiographql.client.request import GraphQLRequestContainer


@dataclass(frozen=True)
class GraphQLBaseResponse(GraphQLRequestContainer):
    json: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class GraphQLResponse(GraphQLBaseResponse):
    """
    GraphQL Response object wrapping response data and any errors. This object also
    contains the a copy of the :class:`GraphQLRequest` that produced this response.
    """

    @property
    def errors(self) -> List[GraphQLError]:
        """
        A list of :class:`GraphQLError` objects if server responded with query errors.
        """
        return [GraphQLError.load(error) for error in self.json.get("errors", list())]

    @property
    def data(self) -> Dict[str, Any]:
        """The data payload the server responded with."""
        return self.json.get("data", dict())

    @property
    def query(self) -> str:
        """The query string used to produce this response."""
        return self.request.query
