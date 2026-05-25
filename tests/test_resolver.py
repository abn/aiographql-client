from __future__ import annotations

import importlib.metadata

from unittest.mock import patch

import pytest

from aiographql.client.transport.resolver import _is_module_available
from aiographql.client.transport.resolver import get_default_subscription_transport
from aiographql.client.transport.resolver import get_default_transport


def test_resolver_is_module_available_version_check() -> None:
    with patch("aiographql.client.transport.resolver.importlib") as mock_importlib:
        mock_importlib.metadata.PackageNotFoundError = (
            importlib.metadata.PackageNotFoundError
        )
        mock_importlib.metadata.version.return_value = "0.23.0"
        assert _is_module_available("httpx", min_version="0.24.0") is False

        mock_importlib.metadata.version.return_value = "0.24.0"
        assert _is_module_available("httpx", min_version="0.24.0") is True

        mock_importlib.import_module.side_effect = ImportError
        assert _is_module_available("httpx") is False


def test_resolver_no_transport_available() -> None:
    with patch(
        "aiographql.client.transport.resolver._is_module_available",
        return_value=False,
    ):
        with pytest.raises(RuntimeError, match="No suitable transport found"):
            get_default_transport("http://test")

        with pytest.raises(
            RuntimeError, match="No suitable subscription transport found"
        ):
            get_default_subscription_transport("http://test")
