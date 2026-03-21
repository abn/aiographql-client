from __future__ import annotations

import pytest

import aiographql.client


def test_aiographql_client_getattr_attribute_error() -> None:
    with pytest.raises(AttributeError) as excinfo:
        _ = aiographql.client.NonExistentAttribute
    assert "module 'aiographql.client' has no attribute 'NonExistentAttribute'" in str(
        excinfo.value
    )


def test_aiographql_client_getattr_aiohttp_transport() -> None:
    from aiographql.client.transport import AiohttpTransport

    assert aiographql.client.AiohttpTransport is AiohttpTransport


def test_aiographql_client_getattr_httpx_transport() -> None:
    try:
        from aiographql.client.transport import HttpxTransport

        assert aiographql.client.HttpxTransport is HttpxTransport
    except ImportError:
        pytest.skip("httpx not installed")
