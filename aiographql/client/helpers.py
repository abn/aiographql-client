import aiohttp


async def create_default_connector() -> aiohttp.TCPConnector:
    return aiohttp.TCPConnector(force_close=True, limit=1, enable_cleanup_closed=True)
