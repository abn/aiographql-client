import dataclasses
from typing import Any, Dict, List

from aiographql.client.error import GraphQLError
from aiographql.client.request import GraphQLRequestContainer


@dataclasses.dataclass(frozen=True)
class GraphQLBaseResponse(GraphQLRequestContainer):
    json: Dict[str, Any] = dataclasses.field(default_factory=dict)


@dataclasses.dataclass(frozen=True)
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
        errors = self.json.get("errors")
        if errors is None:
            return []
        return [GraphQLError.load(error) for error in errors]

    @property
    def data(self) -> Dict[str, Any]:
        """The data payload the server responded with."""
        data = self.json.get("data")
        return data if isinstance(data, dict) else dict()

    @property
    def query(self) -> str:
        """The query string used to produce this response."""
        if isinstance(self.request, str):
            return self.request
        return self.request.query
