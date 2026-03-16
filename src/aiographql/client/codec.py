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
from typing import cast
from typing import get_args
from typing import get_type_hints
from typing import runtime_checkable

from aiographql.client.exceptions import GraphQLCodecException


try:
    import pydantic

    from pydantic import BaseModel
except ImportError:
    pydantic = None  # type: ignore[assignment]
    BaseModel = None  # type: ignore[assignment, misc]


if TYPE_CHECKING:
    from collections.abc import Callable


T = TypeVar("T")


@runtime_checkable
class GraphQLCodec(Protocol):
    def encode(self, value: Any, include_primitives: bool = True) -> Any: ...

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

    def encode(self, value: Any, include_primitives: bool = True) -> Any:
        if value is None or isinstance(value, (str, int, float, bool)):
            return value

        if include_primitives and type(value) in self._encoders:
            return self._encoders[type(value)](value)

        if include_primitives and isinstance(value, enum.Enum):
            return value.value

        if dataclasses.is_dataclass(value):
            return {
                f.name: self.encode(
                    getattr(value, f.name), include_primitives=include_primitives
                )
                for f in dataclasses.fields(value)
            }

        if isinstance(value, BaseModel):
            return self.encode(
                value.model_dump(), include_primitives=include_primitives
            )

        if isinstance(value, (list, tuple, set)):
            return [
                self.encode(item, include_primitives=include_primitives)
                for item in value
            ]

        if isinstance(value, dict):
            return {
                k: self.encode(v, include_primitives=include_primitives)
                for k, v in value.items()
            }

        # Fallback for subclasses or unhandled types
        if include_primitives:
            for base_type, encoder in self._encoders.items():
                if isinstance(value, base_type):
                    return encoder(value)

        return value

    def decode(self, value: Any, target_type: type[T]) -> T:
        if value is None:
            return value  # type: ignore[return-value]

        origin = getattr(target_type, "__origin__", None)
        if origin is not None:
            args = get_args(target_type)
            if origin is list or origin is Iterable:
                item_type = args[0]
                return [self.decode(item, item_type) for item in value]  # type: ignore[return-value]
            if origin is dict:
                key_type, val_type = args
                return {
                    self.decode(k, key_type): self.decode(v, val_type)
                    for k, v in value.items()
                }  # type: ignore[return-value]
            if origin is Union:
                # Simple Union support: try each type until one works
                for arg in args:
                    if arg is type(None) and value is None:
                        return cast("T", None)
                    try:
                        return self.decode(value, arg)  # type: ignore[no-any-return]
                    except (ValueError, TypeError, GraphQLCodecException):
                        continue
                raise GraphQLCodecException(f"Cannot decode {value} to {target_type}")

        if target_type in self._decoders:
            try:
                return cast("T", self._decoders[target_type](value))
            except Exception as e:
                raise GraphQLCodecException(
                    f"Failed to decode {value} to {target_type}: {e}"
                ) from e

        if isinstance(target_type, type) and issubclass(target_type, enum.Enum):  # type: ignore[redundant-expr]
            return target_type(value)

        if dataclasses.is_dataclass(target_type):
            if not isinstance(value, dict):
                raise GraphQLCodecException(
                    f"Cannot decode non-dict value {value} to dataclass {target_type}"
                )
            field_types = get_type_hints(target_type)
            kwargs = {}
            for k, v in value.items():
                if k in field_types:
                    kwargs[k] = self.decode(v, field_types[k])
                else:
                    kwargs[k] = v
            return target_type(**kwargs)

        if issubclass(target_type, BaseModel):
            if not isinstance(value, dict):
                raise GraphQLCodecException(
                    f"Cannot decode non-dict value {value} to Pydantic model {target_type}"
                )
            try:
                return target_type.model_validate(value)
            except Exception as e:
                raise GraphQLCodecException(
                    f"Failed to validate Pydantic model {target_type}: {e}"
                ) from e

        try:
            if isinstance(target_type, type):
                if isinstance(value, target_type):
                    return value
                return target_type(value)  # type: ignore[call-arg]
            return value
        except (ValueError, TypeError):
            raise
        except Exception as e:
            raise GraphQLCodecException(
                f"Failed to decode {value} to {target_type}: {e}"
            ) from e
