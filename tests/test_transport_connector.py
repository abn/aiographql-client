from __future__ import annotations

import pytest


pytest.importorskip("aiohttp")

import aiohttp

from aiographql.client.transport.aiohttp import AiohttpTransport


@pytest.mark.asyncio
async def test_create_default_connector() -> None:
    connector = await AiohttpTransport.create_default_connector()
    assert isinstance(connector, aiohttp.TCPConnector)
    assert connector.force_close is True
    assert connector.limit == 100
    # Clean up the connector
    await connector.close()
