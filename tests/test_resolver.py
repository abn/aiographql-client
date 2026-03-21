from __future__ import annotations

import importlib.metadata
from unittest.mock import patch

import pytest

from aiographql.client.transport.resolver import (
    _is_httpx_available,
    get_default_subscription_transport,
    get_default_transport,
)


def test_resolver_is_httpx_available_version_check() -> None:
    with patch("importlib.metadata.version", return_value="0.23.0"):
        assert _is_httpx_available(min_version="0.24.0") is False
    with patch("importlib.metadata.version", return_value="0.24.0"):
        assert _is_httpx_available(min_version="0.24.0") is True
    with patch(
        "importlib.metadata.version",
        side_effect=importlib.metadata.PackageNotFoundError,
    ):
        assert _is_httpx_available() is False


def test_resolver_explicit_transport_not_found() -> None:
    with (
        patch(
            "aiographql.client.transport.resolver._is_httpx_available",
            return_value=False,
        ),
        pytest.raises(ImportError, match="httpx is not installed"),
    ):
        get_default_transport("http://test", transport="httpx")

    with (
        patch(
            "aiographql.client.transport.resolver._is_aiohttp_available",
            return_value=False,
        ),
        pytest.raises(ImportError, match="aiohttp is not installed"),
    ):
        get_default_transport("http://test", transport="aiohttp")


def test_resolver_subscription_explicit_transport_not_found() -> None:
    with (
        patch(
            "aiographql.client.transport.resolver._is_aiohttp_available",
            return_value=False,
        ),
        pytest.raises(ImportError, match="aiohttp is not installed"),
    ):
        get_default_subscription_transport("http://test", transport="aiohttp")


def test_resolver_no_transport_available() -> None:
    with (
        patch(
            "aiographql.client.transport.resolver._is_aiohttp_available",
            return_value=False,
        ),
        patch(
            "aiographql.client.transport.resolver._is_httpx_available",
            return_value=False,
        ),
    ):
        with pytest.raises(RuntimeError, match="No suitable transport found"):
            get_default_transport("http://test")

        with pytest.raises(
            RuntimeError, match="No suitable subscription transport found"
        ):
            get_default_subscription_transport("http://test")
