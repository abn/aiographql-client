import dataclasses
from typing import Any, Dict, List, Optional, Type, TypeVar, Union

T = TypeVar("T", bound="GraphQLError")


@dataclasses.dataclass(frozen=True)
class GraphQLError:
    """
    GraphQL error response object.
    """

    extensions: Dict[str, Any] = dataclasses.field(default_factory=dict)
    locations: Optional[List[Dict[str, int]]] = dataclasses.field(default=None)
    message: Optional[str] = dataclasses.field(default=None)
    path: Optional[List[Union[str, int]]] = dataclasses.field(default=None)

    @classmethod
    def load(cls: Type[T], data: Dict[str, Any]) -> T:
        construct_class = cls
        custom_keys = [
            key
            for key in data.keys()
            if key not in {field.name for field in dataclasses.fields(cls)}
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
