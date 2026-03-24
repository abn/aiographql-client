from __future__ import annotations

from aiographql.client.serializer import JSONSerializer
from aiographql.client.serializer import OrjsonSerializer


def test_json_serializer_coverage() -> None:
    serializer = JSONSerializer()
    data = {"a": 1}
    serialized = serializer.dumps(data)
    assert isinstance(serialized, str)
    assert serializer.loads(serialized) == data


def test_orjson_serializer_coverage() -> None:
    serializer = OrjsonSerializer()
    data = {"a": 1}
    serialized = serializer.dumps(data)
    assert isinstance(serialized, bytes)
    assert serializer.loads(serialized) == data
