from __future__ import annotations

import importlib.metadata

from unittest.mock import patch

import pytest

from aiographql.client.transport.resolver import _is_httpx_available
from aiographql.client.transport.resolver import get_default_subscription_transport
from aiographql.client.transport.resolver import get_default_transport


@pytest.mark.httpx
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
        patch(
            "aiographql.client.transport.resolver._is_websockets_available",
            return_value=False,
        ),
    ):
        with pytest.raises(RuntimeError, match="No suitable transport found"):
            get_default_transport("http://test")

        with pytest.raises(
            RuntimeError, match="No suitable subscription transport found"
        ):
            get_default_subscription_transport("http://test")
