from dataclasses import dataclass, field, fields, make_dataclass
from typing import Any, Dict, List, Optional, Type, TypeVar, Union

T = TypeVar("T", bound="GraphQLError")


@dataclass(frozen=True)
class GraphQLError:
    """
    GraphQL error response object.
    """

    extensions: Dict[str, Any] = field(default_factory=dict)
    locations: Optional[List[Dict[str, int]]] = field(default=None)
    message: Optional[str] = field(default=None)
    path: Optional[List[Union[str, int]]] = field(default=None)

    @classmethod
    def load(cls: Type[T], data: Dict[str, Any]) -> T:
        construct_class = cls
        custom_keys = [
            key
            for key in data.keys()
            if key not in {field.name for field in fields(cls)}
        ]

        if custom_keys:
            custom_fields = [
                (key, type(data[key]), field(default=None)) for key in custom_keys
            ]
            construct_class = make_dataclass(
                "CustomGraphQLError",
                fields=custom_fields,
                bases=(GraphQLError,),
                frozen=True,
            )

        return construct_class(**data)
