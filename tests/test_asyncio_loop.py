import asyncio
import gc
from typing import Any, AsyncGenerator, Dict, List, Tuple

import pytest

from aiographql.client import GraphQLClient, GraphQLRequest

pytestmark = pytest.mark.asyncio


@pytest.fixture
async def event_loop_exceptions() -> (
    AsyncGenerator[List[Tuple[None, Dict[str, Any]]], None]
):
    running_loop = asyncio.get_running_loop()
    exceptions: List[Tuple[None, Dict[str, Any]]] = list()

    def exception_handler(_: Any, context: Dict[str, Any]) -> None:
        nonlocal exceptions
        exceptions.append((None, context))

    old_handler = running_loop.get_exception_handler()
    running_loop.set_exception_handler(exception_handler)

    yield exceptions

    running_loop.set_exception_handler(old_handler)


async def test_helper_implicit_aiohttp_client_session_is_closed(
    event_loop_exceptions: List[Tuple[None, Dict[str, Any]]],
    client: GraphQLClient,
    headers: Dict[str, str],
    query_city: str,
) -> None:
    request = GraphQLRequest(query=query_city, headers=headers)
    await client.query(request)

    # force python to gc unclosed sessions
    gc.collect()

    for _, context in event_loop_exceptions:
        # we check the message and that it is not related to any persistent session
        if context["message"] == "Unclosed client session":
            pytest.fail(f"Found unclosed client session: {context}")
