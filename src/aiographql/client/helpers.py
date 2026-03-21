from __future__ import annotations

import sys
import warnings

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING
from typing import Any


if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    import aiohttp


@asynccontextmanager
async def aiohttp_client_session() -> AsyncGenerator[aiohttp.ClientSession, None]:
    try:
        import aiohttp
    except ImportError:
        from aiographql.client.exceptions import GraphQLClientException

        raise GraphQLClientException(
            "aiohttp is required to use this feature. "
            "Install it with `pip install aiographql-client[aiohttp]`."
        ) from None

    with warnings.catch_warnings():
        # ignore:  DeprecationWarning: The loop argument is deprecated since
        # Python 3.8, and scheduled for removal in Python 3.10.
        warnings.filterwarnings(
            action="ignore",
            message=r"The loop argument is deprecated since Python 3.8",
            category=DeprecationWarning,
            module="aiohttp.connector",
        )
        connector_kwargs: dict[str, Any] = {"force_close": True, "limit": 1}
        if sys.version_info < (3, 14):
            connector_kwargs["enable_cleanup_closed"] = True

        connector = aiohttp.TCPConnector(**connector_kwargs)
        session = aiohttp.ClientSession(connector=connector)
        yield session

        # close session explicitly as part of context cleanup
        await session.close()


async def create_default_connector() -> aiohttp.TCPConnector:
    try:
        import aiohttp
    except ImportError:
        from aiographql.client.exceptions import GraphQLClientException

        raise GraphQLClientException(
            "aiohttp is required to use this feature. "
            "Install it with `pip install aiographql-client[aiohttp]`."
        ) from None

    connector_kwargs: dict[str, Any] = {"force_close": True, "limit": 1}
    if sys.version_info < (3, 14):
        connector_kwargs["enable_cleanup_closed"] = True

    return aiohttp.TCPConnector(**connector_kwargs)
