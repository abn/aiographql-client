from __future__ import annotations

from aiographql.client.serializer import JSONSerializer


def test_json_serializer_coverage() -> None:
    serializer = JSONSerializer()
    data = {"a": 1}
    serialized = serializer.dumps(data)
    assert isinstance(serialized, str)
    assert serializer.loads(serialized) == data
