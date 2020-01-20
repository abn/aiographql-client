from __future__ import annotations

from copy import deepcopy
from dataclasses import InitVar, asdict, dataclass, field, replace
from typing import Any, Dict, List, Optional

import graphql
import ujson as json


@dataclass(frozen=True)
class GraphQLError:
    extensions: Dict[str, Any] = field(default_factory=dict)
    message: Optional[str] = field(default=None)


@dataclass
class GraphQLRequest:
    query: str
    operationName: Optional[str] = field(default=None)
    variables: Dict[str, Any] = field(default_factory=dict)
    validate: bool = field(default=True)
    headers: Dict[str, str] = field(default_factory=dict)
    schema: Optional[graphql.GraphQLSchema] = None

    def __post_init__(self) -> None:
        pass

    @staticmethod
    def _coerce_value(value: Any) -> Any:
        if isinstance(value, bool):
            return int(value)
        if isinstance(value, dict):
            return json.dumps(value)
        return value

    def payload(self, coerce: bool = False) -> Dict[str, Any]:
        return {
            k: v if not coerce else self._coerce_value(v)
            for k, v in asdict(self).items()
            if v is not None and k not in {"schema", "headers", "validate"}
        }

    def copy(
        self,
        headers: Optional[Dict[str, str]] = None,
        headers_fallback: Optional[Dict[str, str]] = None,
        operation: Optional[str] = None,
        variables: Optional[Dict[str, Any]] = None,
    ) -> GraphQLRequest:
        return replace(
            self,
            operationName=operation or self.operationName,
            variables={**deepcopy(self.variables), **(variables or dict())},
            headers={
                **(headers_fallback or dict()),
                **self.headers,
                **(headers or dict()),
            },
        )


@dataclass(frozen=True)
class GraphQLRequestContainer:
    request: GraphQLRequest
    headers: InitVar[Optional[Dict[str, str]]] = field(default=None)
    operation: InitVar[Optional[str]] = field(default=None)
    variables: InitVar[Optional[Dict[str, Any]]] = field(default=None)

    def __post_init__(
        self,
        headers: Optional[Dict[str, str]] = None,
        operation: Optional[str] = None,
        variables: Optional[Dict[str, Any]] = None,
    ):
        object.__setattr__(
            self,
            "request",
            self.request.copy(
                headers=headers, operation=operation, variables=variables
            ),
        )


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
