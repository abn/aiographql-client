from __future__ import annotations

import dataclasses
from copy import deepcopy
from typing import Any, Dict, Optional

import ujson as json


@dataclasses.dataclass(frozen=True)
class GraphQLRequest:
    """
    GraphQL Request object that can be reused or used to store multiple named queries
    with default *operationName`, *variables* and *header* to use.

    :param query: GraphQL query string.
    :param operation: Optional name of operation to use from the query.
    :param variables: Variable dictionary pass with the query to the server.
    :param validate: If `True`, the request query is validated against the latest available
        schema from the server.
    :param headers: Headers to use, in addition to client default headers when making
        the HTTP request.
    """

    query: str
    operation: dataclasses.InitVar[Optional[str]] = dataclasses.field(default=None)
    operationName: Optional[str] = dataclasses.field(default=None, init=False)
    variables: Dict[str, Any] = dataclasses.field(default_factory=dict)
    validate: bool = dataclasses.field(default=True)
    headers: Dict[str, str] = dataclasses.field(default_factory=dict)

    def __post_init__(self, operation: Optional[str] = None):
        for name in {"headers", "variables"}:
            if getattr(self, name) is None:
                object.__setattr__(self, name, dict())

        if operation is not None:
            object.__setattr__(self, "operationName", operation)

    def __getattr__(self, item):
        if item == "operation":
            return self.operationName
        return super(GraphQLRequest, self).__getattribute__(item)

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
            for k, v in dataclasses.asdict(self).items()
            if v is not None and k not in {"schema", "headers", "validate"}
        }

    def copy(
        self,
        headers: Optional[Dict[str, str]] = None,
        headers_fallback: Optional[Dict[str, str]] = None,
        operation: Optional[str] = None,
        variables: Optional[Dict[str, Any]] = None,
    ) -> GraphQLRequest:
        return dataclasses.replace(
            self,
            operation=operation or self.operationName,
            variables={**deepcopy(self.variables), **(variables or dict())},
            headers={
                **(headers_fallback or dict()),
                **self.headers,
                **(headers or dict()),
            },
        )


@dataclasses.dataclass(frozen=True)
class GraphQLRequestContainer:
    request: GraphQLRequest
    headers: dataclasses.InitVar[Optional[Dict[str, str]]] = dataclasses.field(
        default=None
    )
    operation: dataclasses.InitVar[Optional[str]] = dataclasses.field(default=None)
    variables: dataclasses.InitVar[Optional[Dict[str, Any]]] = dataclasses.field(
        default=None
    )

    def __post_init__(
        self,
        headers: Optional[Dict[str, str]] = None,
        operation: Optional[str] = None,
        variables: Optional[Dict[str, Any]] = None,
    ):
        object.__setattr__(
            self,
            "request",
            (
                GraphQLRequest(query=self.request)
                if isinstance(self.request, str)
                else self.request.copy(
                    headers=headers, operation=operation, variables=variables
                )
            ),
        )
