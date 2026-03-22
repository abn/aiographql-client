from __future__ import annotations

import dataclasses
import enum
import uuid

from typing import TYPE_CHECKING
from typing import Any
from typing import cast

import pytest


if TYPE_CHECKING:
    from pydantic import BaseModel

from aiographql.client.codec import DefaultGraphQLCodec
from aiographql.client.exceptions import GraphQLCodecException


class Color(enum.Enum):
    RED = "red"
    GREEN = "green"


@dataclasses.dataclass
class User:
    id: uuid.UUID
    name: str


def get_pydantic_model() -> type[BaseModel]:
    from pydantic import BaseModel

    class MyPydanticModel(BaseModel):
        id: int
        name: str

    return MyPydanticModel


def test_encode_fallback_subclasses() -> None:
    codec = DefaultGraphQLCodec()

    class MyUUID(uuid.UUID):
        pass

    u = MyUUID(int=1)
    # This should hit lines 106-108 in encode()
    assert codec.encode(u) == str(u)

    # Test with include_primitives=False to hit line 110
    assert codec.encode(u, include_primitives=False) is u


@pytest.mark.pydantic
def test_encode_pydantic() -> None:
    pydantic_model = get_pydantic_model()
    codec = DefaultGraphQLCodec()
    model = pydantic_model(id=1, name="test")
    # Hits lines 87-90 in encode()
    assert codec.encode(model) == {"id": 1, "name": "test"}


def test_decode_iterable() -> None:
    codec = DefaultGraphQLCodec()
    data = [1, 2, 3]
    # Hits lines 119-121 in decode() with Iterable
    decoded = codec.decode(data, list[int])
    assert decoded == [1, 2, 3]


def test_decode_dict() -> None:
    codec = DefaultGraphQLCodec()
    data = {"1": "a", "2": "b"}
    # Hits lines 122-127 in decode()
    decoded = codec.decode(data, cast("Any", dict[int, str]))
    assert decoded == {1: "a", 2: "b"}


def test_decode_union() -> None:
    codec = DefaultGraphQLCodec()
    # Hits lines 128-137 in decode()
    assert codec.decode("123", cast("Any", int | str)) == 123
    assert codec.decode("abc", cast("Any", int | str)) == "abc"
    assert codec.decode(None, cast("Any", int | None)) is None

    # This should fail all Union branches: Union[int, float]
    # It will try int("abc") -> ValueError, then float("abc") -> ValueError.
    # Finally it should raise GraphQLCodecException.
    with pytest.raises(GraphQLCodecException, match="Cannot decode"):
        codec.decode("abc", cast("Any", int | float))


def test_decode_dataclass_non_dict_failure() -> None:
    codec = DefaultGraphQLCodec()
    # Hits line 151-154
    with pytest.raises(GraphQLCodecException, match="Cannot decode non-dict value"):
        codec.decode("not-a-dict", User)


def test_decode_dataclass_extra_fields() -> None:
    codec = DefaultGraphQLCodec()
    data = {"id": str(uuid.uuid4()), "name": "John", "extra": "field"}
    # Hits line 161 (else branch in dataclass decoding loop)
    # The TypeError from User(**kwargs) is caught at lines 185-187
    with pytest.raises(GraphQLCodecException, match="Failed to decode"):
        codec.decode(data, User)


@pytest.mark.pydantic
def test_decode_pydantic_success() -> None:
    pydantic_model = get_pydantic_model()
    codec = DefaultGraphQLCodec()
    data = {"id": 1, "name": "test"}
    # Hits lines 164-170
    model = codec.decode(data, pydantic_model)
    assert isinstance(model, pydantic_model)
    assert model.id == 1  # type: ignore[attr-defined]


@pytest.mark.pydantic
def test_decode_pydantic_failure() -> None:
    pydantic_model = get_pydantic_model()
    codec = DefaultGraphQLCodec()
    # Hits lines 165-168
    with pytest.raises(
        GraphQLCodecException,
        match=r"Cannot decode non-dict value .* to Pydantic model",
    ):
        codec.decode("not-a-dict", pydantic_model)

    # Hits lines 171-174
    with pytest.raises(
        GraphQLCodecException, match="Failed to validate Pydantic model"
    ):
        codec.decode({"id": "not-an-int"}, pydantic_model)


def test_decode_general_fallback() -> None:
    codec = DefaultGraphQLCodec()
    # Hits lines 178-179
    assert codec.decode(123, int) == 123

    # Hits line 180 (instantiating target_type(value))
    assert codec.decode("123", int) == 123


def test_decode_general_failure() -> None:
    codec = DefaultGraphQLCodec()

    # Hits lines 184-187
    class FailingType:
        def __init__(self, val: Any) -> None:
            raise RuntimeError("Failed")

    with pytest.raises(GraphQLCodecException, match="Failed to decode"):
        codec.decode("val", FailingType)


def test_decode_none() -> None:
    codec = DefaultGraphQLCodec()
    # Hits line 113-114
    assert codec.decode(None, int) is None


def test_decode_union_none() -> None:
    codec = DefaultGraphQLCodec()
    # Hits line 132
    assert codec.decode(None, cast("Any", int | None)) is None
