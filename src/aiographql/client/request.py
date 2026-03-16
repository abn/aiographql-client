from __future__ import annotations

import dataclasses

from copy import deepcopy
from typing import TYPE_CHECKING
from typing import Any
from typing import cast


if TYPE_CHECKING:
    from aiographql.client.codec import GraphQLCodec


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
    operation: dataclasses.InitVar[str | None] = None
    operationName: str | None = dataclasses.field(default=None, init=False)
    variables: dict[str, Any] = dataclasses.field(default_factory=dict)
    validate: bool = True
    headers: dict[str, str] = dataclasses.field(default_factory=dict)
    codec: GraphQLCodec | None = dataclasses.field(default=None, compare=False)

    def __post_init__(self, operation: str | None) -> None:
        if operation is not None:
            object.__setattr__(self, "operationName", operation)

    def __getattr__(self, item: str) -> Any:
        if item == "operation":
            return self.operationName
        return super().__getattribute__(item)

    def payload(self) -> dict[str, Any]:
        from aiographql.client.codec import DefaultGraphQLCodec

        codec = self.codec or DefaultGraphQLCodec()
        payload = {
            "query": self.query,
            "variables": cast("DefaultGraphQLCodec", codec).encode(
                self.variables, include_primitives=False
            )
            if self.variables
            else {},
        }
        if self.operationName is not None:
            payload["operationName"] = self.operationName
        return payload

    def asdict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "operationName": self.operationName,
            "variables": self.variables,
        }

    def copy(
        self,
        headers: dict[str, str] | None = None,
        headers_fallback: dict[str, str] | None = None,
        operation: str | None = None,
        variables: dict[str, Any] | None = None,
        codec: GraphQLCodec | None = None,
    ) -> GraphQLRequest:
        return dataclasses.replace(
            self,
            operation=operation or self.operationName,
            variables={**deepcopy(self.variables), **(variables or {})},
            headers={
                **(headers_fallback or {}),
                **self.headers,
                **(headers or {}),
            },
            codec=codec or self.codec,
        )


@dataclasses.dataclass(frozen=True)
class GraphQLRequestContainer:
    request: GraphQLRequest | str
    headers: dataclasses.InitVar[dict[str, str] | None] = None
    operation: dataclasses.InitVar[str | None] = None
    variables: dataclasses.InitVar[dict[str, Any] | None] = None
    codec: dataclasses.InitVar[GraphQLCodec | None] = None

    def __post_init__(
        self,
        headers: dict[str, str] | None,
        operation: str | None,
        variables: dict[str, Any] | None,
        codec: GraphQLCodec | None,
    ) -> None:
        object.__setattr__(
            self,
            "request",
            (
                GraphQLRequest(query=self.request, codec=codec)
                if isinstance(self.request, str)
                else self.request.copy(
                    headers=headers,
                    operation=operation,
                    variables=variables,
                    codec=codec,
                )
            ),
        )
