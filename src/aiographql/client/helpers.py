from __future__ import annotations

import sys

from typing import TYPE_CHECKING
from typing import Any


if TYPE_CHECKING:
    import aiohttp


async def create_default_connector() -> aiohttp.TCPConnector:
    try:
        import aiohttp
    except ImportError:
        from aiographql.client.exceptions import GraphQLClientException

        raise GraphQLClientException(
            "aiohttp is required to use this feature. "
            "Install it with `pip install aiographql-client[aiohttp]`."
        ) from None

    connector_kwargs: dict[str, Any] = {"force_close": True, "limit": 10}
    if sys.version_info < (3, 14):
        connector_kwargs["enable_cleanup_closed"] = True

    return aiohttp.TCPConnector(**connector_kwargs)
