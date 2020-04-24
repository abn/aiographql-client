from dataclasses import dataclass, field
from typing import Dict, Any, List

from aiographql.client.error import GraphQLError
from aiographql.client.request import GraphQLRequestContainer

BASE_ERROR_FIELDS = {"extensions", "locations", "message"}


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
        errors = self.json.get("errors", list())
        error_list = []
        for error in errors:
            error_fields = {
                field: value
                for field, value in error.items()
                if field in BASE_ERROR_FIELDS
            }
            unknown_error_fields = {
                field: value
                for field, value in error.items()
                if field not in BASE_ERROR_FIELDS
            }

            error_fields.setdefault("extensions", {})["_unknown_fields"] = unknown_error_fields
            error_list.append(GraphQLError(**error_fields))

        return error_list

    @property
    def data(self) -> Dict[str, Any]:
        """The data payload the server responded with."""
        return self.json.get("data", dict())

    @property
    def query(self) -> str:
        """The query string used to produce this response."""
        return self.request.query
