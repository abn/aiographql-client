import asyncio
import gc

import pytest

from aiographql.client import GraphQLRequest

pytestmark = pytest.mark.asyncio


@pytest.fixture
def event_loop():
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def event_loop_exceptions(event_loop):
    exceptions = list()

    def exception_handler(exc, context):
        nonlocal exceptions
        exceptions.append((exc, context))

    event_loop.set_exception_handler(exception_handler)

    return exceptions


async def test_helper_implicit_aiohttp_client_session_is_closed(
    event_loop, event_loop_exceptions, client, headers, query_city
):
    request = GraphQLRequest(query=query_city, headers=headers)
    await client.query(request)

    # force python to gc unclosed sessions
    gc.collect()

    for exc, context in event_loop_exceptions:
        assert context["message"] != "Unclosed client session"
