from __future__ import annotations

import dataclasses
import datetime
import decimal
import enum
import uuid

import pytest

from aiographql.client.codec import DefaultGraphQLCodec
from aiographql.client.exceptions import GraphQLCodecException


class Color(enum.Enum):
    RED = "red"
    GREEN = "green"


@dataclasses.dataclass
class User:
    id: uuid.UUID
    name: str
    joined_at: datetime.datetime
    balance: decimal.Decimal
    tags: list[str]
    color: Color
    metadata: dict[str, str] | None = None


def test_codec_encode_primitives() -> None:
    codec = DefaultGraphQLCodec()
    assert codec.encode(1) == 1
    assert codec.encode("test") == "test"
    assert codec.encode(True) is True
    assert codec.encode(None) is None


def test_codec_encode_complex() -> None:
    codec = DefaultGraphQLCodec()
    dt = datetime.datetime(2023, 1, 1, 12, 0, 0)
    u = uuid.uuid4()
    d = decimal.Decimal("10.50")

    assert codec.encode(dt) == dt.isoformat()
    assert codec.encode(u) == str(u)
    assert codec.encode(d) == "10.50"
    assert codec.encode(Color.RED) == "red"


def test_codec_encode_dataclass() -> None:
    codec = DefaultGraphQLCodec()
    u_id = uuid.uuid4()
    dt = datetime.datetime(2023, 1, 1, 12, 0, 0)
    user = User(
        id=u_id,
        name="John",
        joined_at=dt,
        balance=decimal.Decimal("100.00"),
        tags=["admin", "staff"],
        color=Color.GREEN,
    )

    encoded = codec.encode(user)
    assert encoded == {
        "id": str(u_id),
        "name": "John",
        "joined_at": dt.isoformat(),
        "balance": "100.00",
        "tags": ["admin", "staff"],
        "color": "green",
        "metadata": None,
    }


def test_codec_decode_primitives() -> None:
    codec = DefaultGraphQLCodec()
    assert codec.decode(1, int) == 1
    assert codec.decode("test", str) == "test"
    assert codec.decode("10.5", decimal.Decimal) == decimal.Decimal("10.5")


def test_codec_decode_dataclass() -> None:
    codec = DefaultGraphQLCodec()
    u_id = uuid.uuid4()
    dt = datetime.datetime(2023, 1, 1, 12, 0, 0)
    data = {
        "id": str(u_id),
        "name": "John",
        "joined_at": dt.isoformat(),
        "balance": "100.00",
        "tags": ["admin", "staff"],
        "color": "green",
    }

    user = codec.decode(data, User)
    assert user.id == u_id
    assert user.name == "John"
    assert user.joined_at == dt
    assert user.balance == decimal.Decimal("100.00")
    assert user.tags == ["admin", "staff"]
    assert user.color == Color.GREEN


def test_codec_decode_nested_list() -> None:
    codec = DefaultGraphQLCodec()
    data = [
        {"id": str(uuid.uuid4()), "name": "A"},
        {"id": str(uuid.uuid4()), "name": "B"},
    ]

    @dataclasses.dataclass
    class SimpleUser:
        id: uuid.UUID
        name: str

    users = codec.decode(data, list[SimpleUser])
    assert len(users) == 2
    assert isinstance(users[0], SimpleUser)
    assert isinstance(users[0].id, uuid.UUID)


def test_codec_registration() -> None:
    codec = DefaultGraphQLCodec()
    from typing import Any

    class Custom:
        def __init__(self, val: str) -> None:
            self.val = val

    codec.register_encoder(Custom, lambda x: f"custom:{x.val}")
    codec.register_decoder(Custom, lambda x: Custom(x.split(":")[1]))

    c = Custom("hello")
    encoded: Any = codec.encode(c)
    assert encoded == "custom:hello"

    decoded: Custom = codec.decode(encoded, Custom)
    assert decoded.val == "hello"


def test_codec_decode_failure() -> None:
    codec = DefaultGraphQLCodec()
    with pytest.raises(GraphQLCodecException):
        codec.decode("not-a-uuid", uuid.UUID)


def test_codec_encode_dict() -> None:
    codec = DefaultGraphQLCodec()
    dt = datetime.datetime(2023, 1, 1, 12, 0, 0)
    d = decimal.Decimal("10.50")

    input_dict = {
        "string_val": "test",
        "int_val": 42,
        "bool_val": True,
        "enum_val": Color.GREEN,
        "datetime_val": dt,
        "decimal_val": d,
        "nested_dict": {
            "nested_enum": Color.RED,
            "nested_list": [1, dt, Color.GREEN],
        },
    }

    encoded = codec.encode(input_dict)

    assert encoded == {
        "string_val": "test",
        "int_val": 42,
        "bool_val": True,
        "enum_val": "green",
        "datetime_val": dt.isoformat(),
        "decimal_val": "10.50",
        "nested_dict": {
            "nested_enum": "red",
            "nested_list": [1, dt.isoformat(), "green"],
        },
    }
