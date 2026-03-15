from __future__ import annotations

import datetime
import decimal
import enum
import uuid

import pytest

from pydantic import BaseModel

from aiographql.client.codec import DefaultGraphQLCodec
from aiographql.client.exceptions import GraphQLCodecException


class Color(enum.Enum):
    RED = "red"
    GREEN = "green"


class UserProfile(BaseModel):
    bio: str
    website: str | None = None


class User(BaseModel):
    id: uuid.UUID
    name: str
    joined_at: datetime.datetime
    balance: decimal.Decimal
    tags: list[str]
    color: Color
    profile: UserProfile | None = None
    metadata: dict[str, str] | None = None


def test_pydantic_encode_simple():
    codec = DefaultGraphQLCodec()
    profile = UserProfile(bio="Developer", website="https://example.com")
    encoded = codec.encode(profile)
    assert encoded == {"bio": "Developer", "website": "https://example.com"}


def test_pydantic_encode_nested():
    codec = DefaultGraphQLCodec()
    u_id = uuid.uuid4()
    dt = datetime.datetime(2023, 1, 1, 12, 0, 0)
    user = User(
        id=u_id,
        name="John",
        joined_at=dt,
        balance=decimal.Decimal("100.00"),
        tags=["admin"],
        color=Color.GREEN,
        profile=UserProfile(bio="Developer"),
    )

    encoded = codec.encode(user)
    assert encoded["id"] == str(u_id)
    assert encoded["joined_at"] == dt.isoformat()
    assert encoded["balance"] == "100.00"
    assert encoded["color"] == "green"
    assert encoded["profile"] == {"bio": "Developer", "website": None}
    assert encoded["tags"] == ["admin"]


def test_pydantic_encode_list_dict():
    codec = DefaultGraphQLCodec()
    profiles = [UserProfile(bio="A"), UserProfile(bio="B")]
    encoded_list = codec.encode(profiles)
    assert encoded_list == [
        {"bio": "A", "website": None},
        {"bio": "B", "website": None},
    ]

    mapping = {"u1": UserProfile(bio="A")}
    encoded_dict = codec.encode(mapping)
    assert encoded_dict == {"u1": {"bio": "A", "website": None}}


def test_pydantic_decode_simple():
    codec = DefaultGraphQLCodec()
    data = {"bio": "Developer", "website": "https://example.com"}
    profile = codec.decode(data, UserProfile)
    assert isinstance(profile, UserProfile)
    assert profile.bio == "Developer"
    assert profile.website == "https://example.com"


def test_pydantic_decode_nested():
    codec = DefaultGraphQLCodec()
    u_id = uuid.uuid4()
    dt = datetime.datetime(2023, 1, 1, 12, 0, 0)
    data = {
        "id": str(u_id),
        "name": "John",
        "joined_at": dt.isoformat(),
        "balance": "100.00",
        "tags": ["admin"],
        "color": "green",
        "profile": {"bio": "Developer", "website": None},
    }

    user = codec.decode(data, User)
    assert isinstance(user, User)
    assert user.id == u_id
    assert user.profile.bio == "Developer"
    assert user.balance == decimal.Decimal("100.00")


def test_pydantic_decode_list():
    codec = DefaultGraphQLCodec()
    data = [{"bio": "A"}, {"bio": "B"}]
    profiles = codec.decode(data, list[UserProfile])
    assert len(profiles) == 2
    assert all(isinstance(p, UserProfile) for p in profiles)
    assert profiles[0].bio == "A"


def test_pydantic_decode_invalid_data():
    codec = DefaultGraphQLCodec()
    with pytest.raises(GraphQLCodecException) as excinfo:
        # bio is required
        codec.decode({"website": "http://test.com"}, UserProfile)
    assert "Failed to validate Pydantic model" in str(excinfo.value)


def test_pydantic_decode_non_dict():
    codec = DefaultGraphQLCodec()
    with pytest.raises(GraphQLCodecException) as excinfo:
        codec.decode("not-a-dict", UserProfile)
    assert "Cannot decode non-dict value" in str(excinfo.value)
