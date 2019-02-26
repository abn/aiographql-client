from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Optional, List

import graphql


@dataclass
class GraphQLError:
    extensions: Dict[str, Any] = field(default_factory=dict)
    message: Optional[str] = field(default=None)


@dataclass
class GraphQLRequest:
    query: str
    operationName: str = field(default=None)
    variables: Dict[str, Any] = field(default=None)
    validate: bool = field(default=True)
    schema: Optional[graphql.GraphQLSchema] = None

    def json(self) -> Dict[str, Any]:
        # TODO: serialise variables correctly
        return {
            k: v
            for k, v in asdict(self).items()
            if k not in {"schema"} and v is not None
        }


@dataclass
class GraphQLBaseResponse:
    request: GraphQLRequest
    json: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GraphQLResponse(GraphQLBaseResponse):
    @property
    def errors(self) -> List[GraphQLError]:
        return [GraphQLError(**error) for error in self.json.get("errors", list())]

    @property
    def data(self) -> Dict[str, Any]:
        return self.json.get("data", dict())


@dataclass
class GraphQLTransaction:
    request: GraphQLRequest
    response: GraphQLResponse

    @property
    def query(self):
        return self.request.query

    @property
    def errors(self):
        return self.response.errors

    @property
    def data(self):
        return self.response.data

    @classmethod
    def create(
        cls, request: GraphQLRequest, json: Dict[str, Any]
    ) -> GraphQLTransaction:
        return cls(
            request=request, response=GraphQLResponse(request=request, json=json)
        )
