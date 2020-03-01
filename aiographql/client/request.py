from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field, asdict, replace, InitVar
from typing import Optional, Dict, Any

import ujson as json


@dataclass(frozen=True)
class GraphQLRequest:
    query: str
    operation: InitVar[Optional[str]] = field(default=None)
    operationName: Optional[str] = field(default=None, init=False)
    variables: Dict[str, Any] = field(default_factory=dict)
    validate: bool = field(default=True)
    headers: Dict[str, str] = field(default_factory=dict)

    def __post_init__(self, operation: Optional[str] = None):
        if operation is not None:
            object.__setattr__(self, "operationName", operation)

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
            operation=operation or self.operationName,
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
            GraphQLRequest(query=self.request)
            if isinstance(self.request, str)
            else self.request.copy(
                headers=headers, operation=operation, variables=variables
            ),
        )
