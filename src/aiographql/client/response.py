from __future__ import annotations

import dataclasses

from typing import TYPE_CHECKING
from typing import Any
from typing import TypeVar
from typing import cast

from aiographql.client.error import GraphQLError
from aiographql.client.request import GraphQLRequestContainer


if TYPE_CHECKING:
    from aiographql.client.codec import GraphQLCodec

T = TypeVar("T")


@dataclasses.dataclass(frozen=True)
class GraphQLBaseResponse(GraphQLRequestContainer):
    json: dict[str, Any] = dataclasses.field(default_factory=dict)

    def __post_init__(
        self,
        headers: dict[str, str] | None,
        operation: str | None,
        variables: dict[str, Any] | None,
        codec: GraphQLCodec | None,
    ) -> None:
        super().__post_init__(
            headers=headers,
            operation=operation,
            variables=variables,
            codec=codec,
        )


@dataclasses.dataclass(frozen=True)
class GraphQLResponse(GraphQLBaseResponse):
    """
    GraphQL Response object wrapping response data and any errors. This object also
    contains the a copy of the :class:`GraphQLRequest` that produced this response.
    """

    @property
    def errors(self) -> list[GraphQLError]:
        """
        A list of :class:`GraphQLError` objects if server responded with query errors.
        """
        if self.json is None:
            return []
        errors = self.json.get("errors")
        if errors is None:
            return []
        return [GraphQLError.load(error) for error in errors]

    @property
    def data(self) -> dict[str, Any]:
        """The data payload the server responded with."""
        if self.json is None:
            return {}
        data = self.json.get("data")
        return data if isinstance(data, dict) else {}

    @property
    def query(self) -> str:
        """The query string used to produce this response."""
        if isinstance(self.request, str):
            return self.request
        return self.request.query

    def data_as(
        self,
        result_type: type[T],
        path: str | None = None,
        codec: GraphQLCodec | None = None,
    ) -> T:
        """
        Decode the response data into a Python object of the specified type.

        :param result_type: The type to decode the data into.
        :param path: An optional dot-separated path to the data to decode.
        :param codec: An optional codec to use for decoding. If not provided, it's
            retrieved from the request's client if available.
        """
        from aiographql.client.codec import DefaultGraphQLCodec

        data: Any = self.data
        if path:
            for key in path.split("."):
                if not isinstance(data, dict):
                    raise ValueError(f"Cannot navigate to {path} in {self.data}")
                data = data.get(key)

        codec = codec or getattr(self.request, "codec", None) or DefaultGraphQLCodec()
        return cast("T", codec.decode(data, result_type))
