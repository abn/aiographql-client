import warnings
from contextlib import asynccontextmanager

from typing import AsyncGenerator

import aiohttp


@asynccontextmanager
async def aiohttp_client_session() -> AsyncGenerator[aiohttp.ClientSession, None]:
    with warnings.catch_warnings():
        # ignore:  DeprecationWarning: The loop argument is deprecated since
        # Python 3.8, and scheduled for removal in Python 3.10.
        warnings.filterwarnings(
            action="ignore",
            message=r"The loop argument is deprecated since Python 3.8",
            category=DeprecationWarning,
            module="aiohttp.connector",
        )
        connector = aiohttp.TCPConnector(
            force_close=True, limit=1, enable_cleanup_closed=True
        )
        session = aiohttp.ClientSession(connector=connector)
        yield session

        # close session explicitly as part of context cleanup
        await session.close()


async def create_default_connector() -> aiohttp.TCPConnector:
    return aiohttp.TCPConnector(force_close=True, limit=1, enable_cleanup_closed=True)
