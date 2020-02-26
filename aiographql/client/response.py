from dataclasses import dataclass, field
from typing import Dict, Any, List

from aiographql.client.error import GraphQLError
from aiographql.client.request import GraphQLRequestContainer


@dataclass(frozen=True)
class GraphQLBaseResponse(GraphQLRequestContainer):
    json: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class GraphQLResponse(GraphQLBaseResponse):
    @property
    def errors(self) -> List[GraphQLError]:
        return [GraphQLError(**error) for error in self.json.get("errors", list())]

    @property
    def data(self) -> Dict[str, Any]:
        return self.json.get("data", dict())

    @property
    def query(self):
        return self.request.query
