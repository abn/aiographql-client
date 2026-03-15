from __future__ import annotations

import dataclasses
import datetime
import decimal
import enum
import uuid

from collections.abc import Iterable
from typing import TYPE_CHECKING
from typing import Any
from typing import Protocol
from typing import TypeVar
from typing import Union
from typing import runtime_checkable

from aiographql.client.exceptions import GraphQLCodecException


if TYPE_CHECKING:
    from collections.abc import Callable


T = TypeVar("T")


@runtime_checkable
class GraphQLCodec(Protocol):
    def encode(self, value: Any) -> Any: ...

    def decode(self, value: Any, target_type: type[T]) -> T: ...


class DefaultGraphQLCodec:
    def __init__(self) -> None:
        self._encoders: dict[type, Callable[[Any], Any]] = {
            datetime.datetime: lambda v: v.isoformat(),
            datetime.date: lambda v: v.isoformat(),
            datetime.time: lambda v: v.isoformat(),
            uuid.UUID: str,
            decimal.Decimal: str,
        }
        self._decoders: dict[type, Callable[[Any], Any]] = {
            datetime.datetime: datetime.datetime.fromisoformat,
            datetime.date: datetime.date.fromisoformat,
            datetime.time: datetime.time.fromisoformat,
            uuid.UUID: uuid.UUID,
            decimal.Decimal: decimal.Decimal,
        }

    def register_encoder(self, type_: type, encoder: Callable[[Any], Any]) -> None:
        self._encoders[type_] = encoder

    def register_decoder(self, type_: type, decoder: Callable[[Any], Any]) -> None:
        self._decoders[type_] = decoder

    def encode(self, value: Any) -> Any:
        if value is None or isinstance(value, (str, int, float, bool)):
            return value

        if type(value) in self._encoders:
            return self._encoders[type(value)](value)

        if isinstance(value, enum.Enum):
            return value.value

        if dataclasses.is_dataclass(value):
            return {
                f.name: self.encode(getattr(value, f.name))
                for f in dataclasses.fields(value)
            }

        if isinstance(value, (list, tuple, set)):
            return [self.encode(item) for item in value]

        if isinstance(value, dict):
            return {k: self.encode(v) for k, v in value.items()}

        # Fallback for subclasses or unhandled types
        for base_type, encoder in self._encoders.items():
            if isinstance(value, base_type):
                return encoder(value)

        return value

    def decode(self, value: Any, target_type: type[T]) -> T:
        if value is None:
            return value  # type: ignore[return-value]

        origin = getattr(target_type, "__origin__", None)
        if origin is not None:
            if origin is list or origin is Iterable:
                item_type = target_type.__args__[0]
                return [self.decode(item, item_type) for item in value]  # type: ignore[return-value]
            if origin is dict:
                key_type, val_type = target_type.__args__
                return {
                    self.decode(k, key_type): self.decode(v, val_type)
                    for k, v in value.items()
                }  # type: ignore[return-value]
            if origin is Union:
                # Simple Union support: try each type until one works
                for arg in target_type.__args__:
                    if arg is type(None) and value is None:
                        return None  # type: ignore[return-value]
                    try:
                        return self.decode(value, arg)
                    except (ValueError, TypeError, GraphQLCodecException):
                        continue
                raise GraphQLCodecException(f"Cannot decode {value} to {target_type}")

        if target_type in self._decoders:
            try:
                return self._decoders[target_type](value)
            except Exception as e:
                raise GraphQLCodecException(
                    f"Failed to decode {value} to {target_type}: {e}"
                ) from e

        if isinstance(target_type, type) and issubclass(target_type, enum.Enum):
            return target_type(value)

        if dataclasses.is_dataclass(target_type):
            if not isinstance(value, dict):
                raise GraphQLCodecException(
                    f"Cannot decode non-dict value {value} to dataclass {target_type}"
                )
            field_types = {f.name: f.type for f in dataclasses.fields(target_type)}
            kwargs = {}
            for k, v in value.items():
                if k in field_types:
                    kwargs[k] = self.decode(v, field_types[k])
                else:
                    kwargs[k] = v
            return target_type(**kwargs)

        try:
            if isinstance(value, target_type):
                return value
            return target_type(value)
        except Exception as e:
            raise GraphQLCodecException(
                f"Failed to decode {value} to {target_type}: {e}"
            ) from e
