from __future__ import annotations

import dataclasses

from typing import Any
from typing import TypeVar


T = TypeVar("T", bound="GraphQLError")


@dataclasses.dataclass(frozen=True)
class GraphQLError:
    """
    GraphQL error response object.
    """

    extensions: dict[str, Any] = dataclasses.field(default_factory=dict)
    locations: list[dict[str, int]] | None = dataclasses.field(default=None)
    message: str | None = dataclasses.field(default=None)
    path: list[str | int] | None = dataclasses.field(default=None)

    @classmethod
    def load(cls: type[T], data: dict[str, Any]) -> T:
        construct_class = cls
        cls_fields = {field.name for field in dataclasses.fields(cls)}
        custom_keys = [
            key
            for key in data
            if key not in cls_fields
        ]

        if custom_keys:
            custom_fields = [
                (key, type(data[key]), dataclasses.field(default=None))
                for key in custom_keys
            ]
            construct_class = dataclasses.make_dataclass(
                "CustomGraphQLError",
                fields=custom_fields,
                bases=(GraphQLError,),
                frozen=True,
            )

        return construct_class(**data)
