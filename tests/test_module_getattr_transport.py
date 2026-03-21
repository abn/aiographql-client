from __future__ import annotations

import pytest

from aiographql.client.transport import AiohttpSubscriptionTransport
from aiographql.client.transport import AiohttpTransport
from aiographql.client.transport import HttpxTransport
from aiographql.client.transport.aiohttp import (
    AiohttpSubscriptionTransport as AiohttpSubscriptionTransportActual,
)
from aiographql.client.transport.aiohttp import (
    AiohttpTransport as AiohttpTransportActual,
)
from aiographql.client.transport.httpx import HttpxTransport as HttpxTransportActual


def test_aiohttp_transport_lazy_import() -> None:
    assert AiohttpTransport is AiohttpTransportActual


def test_httpx_transport_lazy_import() -> None:
    assert HttpxTransport is HttpxTransportActual


def test_aiohttp_subscription_transport_lazy_import() -> None:
    assert AiohttpSubscriptionTransport is AiohttpSubscriptionTransportActual


def test_transport_getattr_error() -> None:
    import aiographql.client.transport

    with pytest.raises(
        AttributeError,
        match=r"module 'aiographql.client.transport' has no attribute 'NonExistent'",
    ):
        _ = aiographql.client.transport.NonExistent
