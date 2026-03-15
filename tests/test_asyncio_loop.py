from __future__ import annotations

import asyncio
import gc

from typing import TYPE_CHECKING
from typing import Any

import pytest

from aiographql.client import GraphQLClient
from aiographql.client import GraphQLRequest


if TYPE_CHECKING:
    from collections.abc import AsyncGenerator


pytestmark = pytest.mark.asyncio


@pytest.fixture
async def event_loop_exceptions() -> AsyncGenerator[
    list[tuple[None, dict[str, Any]]], None
]:
    running_loop = asyncio.get_running_loop()
    exceptions: list[tuple[None, dict[str, Any]]] = []

    def exception_handler(_: Any, context: dict[str, Any]) -> None:
        nonlocal exceptions
        exceptions.append((None, context))

    old_handler = running_loop.get_exception_handler()
    running_loop.set_exception_handler(exception_handler)

    yield exceptions

    running_loop.set_exception_handler(old_handler)


async def test_helper_implicit_aiohttp_client_session_is_closed(
    event_loop_exceptions: list[tuple[None, dict[str, Any]]],
    client: GraphQLClient,
    headers: dict[str, str],
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
