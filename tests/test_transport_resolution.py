from __future__ import annotations

import sys

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from aiographql.client import GraphQLClient
from aiographql.client.transport import AiohttpTransport
from aiographql.client.transport import HttpxTransport
from aiographql.client.transport import get_default_transport


def test_get_default_transport_aiohttp_preferred() -> None:
    endpoint = "http://example.com/graphql"
    with patch.dict(sys.modules, {"aiohttp": MagicMock()}):
        transport = get_default_transport(endpoint)
        assert isinstance(transport, AiohttpTransport)
        assert transport.endpoint == endpoint


def test_get_default_transport_aiohttp_missing_fallback_to_httpx() -> None:
    endpoint = "http://example.com/graphql"
    with (
        patch("importlib.metadata.version", return_value="0.24.0"),
        patch.dict(sys.modules, {"aiohttp": None, "httpx": MagicMock()}),
    ):
        transport = get_default_transport(endpoint)
        assert isinstance(transport, HttpxTransport)


def test_get_default_transport_none_available_raises_runtime_error() -> None:
    endpoint = "http://example.com/graphql"
    with (
        patch.dict(sys.modules, {"httpx": None, "aiohttp": None}),
        patch("importlib.metadata.version", side_effect=ImportError),
        pytest.raises(RuntimeError) as excinfo,
    ):
        get_default_transport(endpoint)
        assert "No suitable transport found" in str(excinfo.value)


def test_get_default_transport_passed_instance() -> None:
    endpoint = "http://example.com/graphql"
    mock_transport = MagicMock(spec=HttpxTransport)
    transport = get_default_transport(endpoint, transport=mock_transport)
    assert transport is mock_transport


def test_graphql_client_auto_transport() -> None:
    endpoint = "http://example.com/graphql"
    with patch("aiographql.client.client.get_default_transport") as mock_resolver:
        GraphQLClient(endpoint=endpoint)
        mock_resolver.assert_called_once_with(
            endpoint=endpoint, transport=None, session=None
        )
