from __future__ import annotations

import json

from typing import Any
from typing import Protocol
from typing import runtime_checkable

import orjson


@runtime_checkable
class GraphQLSerializer(Protocol):
    """
    Protocol for JSON serialization/deserialization.
    """

    def loads(self, data: str | bytes) -> Any:
        """
        Deserialize JSON from string or bytes.
        """
        ...

    def dumps(self, value: Any) -> str | bytes:
        """
        Serialize value to JSON string or bytes.
        """
        ...


class OrjsonSerializer:
    """
    Serializer using orjson library.
    """

    def loads(self, data: str | bytes) -> Any:
        return orjson.loads(data)

    def dumps(self, value: Any) -> str | bytes:
        return orjson.dumps(value)


class JSONSerializer:
    """
    Serializer using standard json library.
    """

    def loads(self, data: str | bytes) -> Any:
        return json.loads(data)

    def dumps(self, value: Any) -> str | bytes:
        return json.dumps(value)


DefaultSerializer = OrjsonSerializer
