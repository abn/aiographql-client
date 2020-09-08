import warnings
from contextlib import asynccontextmanager

import aiohttp


@asynccontextmanager
async def aiohttp_client_session():
    with warnings.catch_warnings():
        # ignore:  DeprecationWarning: The loop argument is deprecated since
        # Python 3.8, and scheduled for removal in Python 3.10.
        warnings.filterwarnings(
            action="ignore",
            category=DeprecationWarning,
            module="aiohttp.connector",
            lineno=964,
        )
        connector = aiohttp.TCPConnector(
            force_close=True, limit=1, enable_cleanup_closed=True
        )
        yield aiohttp.ClientSession(connector=connector)


async def create_default_connector() -> aiohttp.TCPConnector:
    return aiohttp.TCPConnector(force_close=True, limit=1, enable_cleanup_closed=True)
