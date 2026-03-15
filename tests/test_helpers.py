import pytest
import aiohttp
from unittest.mock import patch, MagicMock, AsyncMock
from aiographql.client.helpers import create_default_connector, aiohttp_client_session

@pytest.mark.asyncio
async def test_create_default_connector():
    connector = await create_default_connector()
    assert isinstance(connector, aiohttp.TCPConnector)
    assert connector.force_close is True
    assert connector.limit == 1
    assert connector._enable_cleanup_closed is True
    # Clean up the connector
    await connector.close()

@pytest.mark.asyncio
async def test_aiohttp_client_session():
    async with aiohttp_client_session() as session:
        assert isinstance(session, aiohttp.ClientSession)
        connector = session.connector
        assert isinstance(connector, aiohttp.TCPConnector)
        assert connector.force_close is True
        assert connector.limit == 1
        assert connector._enable_cleanup_closed is True

    assert session.closed is True
