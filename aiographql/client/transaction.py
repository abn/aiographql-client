from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Optional, List


@dataclass
class GraphQLError:
    extensions: Dict[str, Any] = field(default_factory=dict)
    message: Optional[str] = field(default=None)


@dataclass
class GraphQLRequest:
    query: str
    operationName: str = field(default=None)
    variables: Dict[str, Any] = field(default=None)

    def json(self) -> Dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class GraphQLResponse:
    json: Dict[str, Any] = field(default_factory=dict)

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
