from __future__ import annotations

import datetime
import decimal
import enum
import uuid

from typing import Any
from typing import cast

import pytest

from aiographql.client.codec import DefaultGraphQLCodec
from aiographql.client.exceptions import GraphQLCodecException


pytestmark = pytest.mark.pydantic


def get_models() -> dict[str, Any]:
    from pydantic import BaseModel

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

    return {"Color": Color, "UserProfile": UserProfile, "User": User}


def test_pydantic_encode_simple() -> None:
    models = get_models()
    user_profile_model = models["UserProfile"]
    codec = DefaultGraphQLCodec()
    profile = user_profile_model(bio="Developer", website="https://example.com")
    encoded = codec.encode(profile)
    assert encoded == {"bio": "Developer", "website": "https://example.com"}


def test_pydantic_encode_nested() -> None:
    models = get_models()
    user_model = models["User"]
    user_profile_model = models["UserProfile"]
    color_enum = models["Color"]
    codec = DefaultGraphQLCodec()
    u_id = uuid.uuid4()
    dt = datetime.datetime(2023, 1, 1, 12, 0, 0)
    user = user_model(
        id=u_id,
        name="John",
        joined_at=dt,
        balance=decimal.Decimal("100.00"),
        tags=["admin"],
        color=color_enum.GREEN,
        profile=user_profile_model(bio="Developer"),
    )

    encoded = codec.encode(user)
    assert encoded["id"] == str(u_id)
    assert encoded["joined_at"] == dt.isoformat()
    assert encoded["balance"] == "100.00"
    assert encoded["color"] == "green"
    assert encoded["profile"] == {"bio": "Developer", "website": None}
    assert encoded["tags"] == ["admin"]


def test_pydantic_encode_list_dict() -> None:
    models = get_models()
    user_profile_model = models["UserProfile"]
    codec = DefaultGraphQLCodec()
    profiles = [user_profile_model(bio="A"), user_profile_model(bio="B")]
    encoded_list = codec.encode(profiles)
    assert encoded_list == [
        {"bio": "A", "website": None},
        {"bio": "B", "website": None},
    ]

    mapping = {"u1": user_profile_model(bio="A")}
    encoded_dict = codec.encode(mapping)
    assert encoded_dict == {"u1": {"bio": "A", "website": None}}


def test_pydantic_decode_simple() -> None:
    models = get_models()
    user_profile_model = models["UserProfile"]
    codec = DefaultGraphQLCodec()
    data = {"bio": "Developer", "website": "https://example.com"}
    profile = codec.decode(data, user_profile_model)
    assert isinstance(profile, user_profile_model)
    assert profile.bio == "Developer"
    assert profile.website == "https://example.com"


def test_pydantic_decode_nested() -> None:
    models = get_models()
    user_model = models["User"]
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

    user = codec.decode(data, user_model)
    assert isinstance(user, user_model)
    assert user.id == u_id
    assert user.profile is not None
    assert user.profile.bio == "Developer"
    assert user.balance == decimal.Decimal("100.00")


def test_pydantic_decode_list() -> None:
    models = get_models()
    user_profile_model = models["UserProfile"]
    codec = DefaultGraphQLCodec()
    data = [{"bio": "A"}, {"bio": "B"}]
    profiles = codec.decode(data, cast("Any", list)[user_profile_model])
    assert isinstance(profiles, list)
    assert len(profiles) == 2
    assert all(isinstance(p, user_profile_model) for p in profiles)
    assert profiles[0].bio == "A"


def test_pydantic_decode_invalid_data() -> None:
    models = get_models()
    user_profile_model = models["UserProfile"]
    codec = DefaultGraphQLCodec()
    with pytest.raises(GraphQLCodecException) as excinfo:
        # bio is required
        codec.decode({"website": "http://test.com"}, user_profile_model)
    assert "Failed to validate Pydantic model" in str(excinfo.value)


def test_pydantic_decode_non_dict() -> None:
    models = get_models()
    user_profile_model = models["UserProfile"]
    codec = DefaultGraphQLCodec()
    with pytest.raises(GraphQLCodecException) as excinfo:
        codec.decode("not-a-dict", user_profile_model)
    assert "Cannot decode non-dict value" in str(excinfo.value)
