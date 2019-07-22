from __future__ import annotations

from dataclasses import asdict, dataclass, field, replace
from typing import Any, Dict, List, Optional

import graphql


@dataclass
class GraphQLError:
    extensions: Dict[str, Any] = field(default_factory=dict)
    message: Optional[str] = field(default=None)


@dataclass
class GraphQLRequest:
    query: str
    operationName: Optional[str] = field(default=None)
    variables: Optional[Dict[str, Any]] = field(default=None)
    validate: bool = field(default=True)
    headers: Dict[str, str] = field(default_factory=dict)
    schema: Optional[graphql.GraphQLSchema] = None

    def __post_init__(self) -> None:
        self.headers = self.headers or dict()

    def asdict(self) -> Dict[str, Any]:
        # TODO: serialise variables correctly
        return {
            k: v
            for k, v in asdict(replace(self, schema=None, headers=None)).items()
            if v is not None
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
