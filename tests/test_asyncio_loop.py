import asyncio
import gc

import pytest

from aiographql.client import GraphQLRequest

pytestmark = pytest.mark.asyncio


@pytest.fixture
async def event_loop_exceptions():
    running_loop = asyncio.get_running_loop()
    exceptions = list()

    def exception_handler(_, context):
        nonlocal exceptions
        exceptions.append((None, context))

    old_handler = running_loop.get_exception_handler()
    running_loop.set_exception_handler(exception_handler)

    yield exceptions

    running_loop.set_exception_handler(old_handler)


async def test_helper_implicit_aiohttp_client_session_is_closed(
    event_loop_exceptions, client, headers, query_city
):
    request = GraphQLRequest(query=query_city, headers=headers)
    await client.query(request)

    # force python to gc unclosed sessions
    gc.collect()

    for _, context in event_loop_exceptions:
        assert context["message"] != "Unclosed client session"
