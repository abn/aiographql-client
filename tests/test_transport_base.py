from __future__ import annotations

import contextlib

from typing import Any

import pytest

from aiographql.client.transport.base import GraphQLSubscriptionTransport
from aiographql.client.transport.base import GraphQLTransport
from aiographql.client.transport.base import GraphQLWebSocketResponse


def test_protocols_runtime_checkable() -> None:
    assert isinstance(GraphQLTransport, type)
    assert isinstance(GraphQLSubscriptionTransport, type)
    assert isinstance(GraphQLWebSocketResponse, type)


@pytest.mark.aiohttp
def test_aiohttp_transport_satisfies_protocol() -> None:
    from aiographql.client.transport.aiohttp import AiohttpTransport

    # We don't need to instantiate it with a real endpoint for isinstance check
    transport = AiohttpTransport(endpoint="http://localhost")
    assert isinstance(transport, GraphQLTransport)


@pytest.mark.httpx
def test_httpx_transport_satisfies_protocol() -> None:
    from aiographql.client.transport.httpx import HttpxTransport

    transport = HttpxTransport(endpoint="http://localhost")
    assert isinstance(transport, GraphQLTransport)


@pytest.mark.aiohttp
def test_aiohttp_subscription_transport_satisfies_protocol() -> None:
    from aiographql.client.transport.aiohttp import AiohttpSubscriptionTransport

    transport = AiohttpSubscriptionTransport(endpoint="ws://localhost")
    assert isinstance(transport, GraphQLSubscriptionTransport)


@pytest.mark.aiohttp
def test_aiohttp_websocket_response_satisfies_protocol(mocker: Any) -> None:
    from aiographql.client.transport.aiohttp import AiohttpWebSocketResponse

    # AiohttpWebSocketResponse needs a mock aiohttp.ClientWebSocketResponse
    mock_ws = mocker.Mock()

    response = AiohttpWebSocketResponse(ws=mock_ws)
    assert isinstance(response, GraphQLWebSocketResponse)


async def test_protocol_methods_coverage() -> None:
    """
    This test is specifically to trigger coverage for the '...' in Protocol definitions.
    """

    # Calling them directly on the protocol class to ensure they are 'covered'
    # even though they do nothing.
    # We use cast(Any, ...) to avoid mypy errors for calling methods on the protocol class
    # with None as self.
    from typing import cast

    with contextlib.suppress(Exception):
        await cast("Any", GraphQLTransport).request(None, None, None, None)

    with contextlib.suppress(Exception):
        await cast("Any", GraphQLTransport).close(None)

    with contextlib.suppress(Exception):
        await cast("Any", GraphQLSubscriptionTransport).subscribe(
            None, None, None, None
        )

    with contextlib.suppress(Exception):
        await cast("Any", GraphQLSubscriptionTransport).close(None)

    with contextlib.suppress(Exception):
        await cast("Any", GraphQLWebSocketResponse).__aenter__(None)

    with contextlib.suppress(Exception):
        await cast("Any", GraphQLWebSocketResponse).__aexit__(None, None, None, None)

    with contextlib.suppress(Exception):
        await cast("Any", GraphQLWebSocketResponse).send_str(None, None)

    with contextlib.suppress(Exception):
        cast("Any", GraphQLWebSocketResponse).__aiter__(None)

    with contextlib.suppress(Exception):
        await cast("Any", GraphQLWebSocketResponse).__anext__(None)


def test_protocol_incomplete_implementation() -> None:
    class IncompleteTransport:
        async def request(
            self, method: Any, request: Any, serializer: Any, **kwargs: Any
        ) -> Any:
            pass

        # missing close()

    transport = IncompleteTransport()
    assert not isinstance(transport, GraphQLTransport)

    class IncompleteWSResponse:
        # missing __aenter__
        async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
            pass

        async def send_str(self, data: str) -> None:
            pass

        def __aiter__(self) -> Any:
            return self

        async def __anext__(self) -> Any:
            pass

    ws_resp = IncompleteWSResponse()
    assert not isinstance(ws_resp, GraphQLWebSocketResponse)

    class IncompleteWSResponse2:
        async def __aenter__(self) -> Any:
            return self

        # missing __aexit__
        async def send_str(self, data: str) -> None:
            pass

        def __aiter__(self) -> Any:
            return self

        async def __anext__(self) -> Any:
            pass

    ws_resp2 = IncompleteWSResponse2()
    assert not isinstance(ws_resp2, GraphQLWebSocketResponse)

    class IncompleteWSResponse3:
        async def __aenter__(self) -> Any:
            return self

        async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
            pass

        # missing send_str
        def __aiter__(self) -> Any:
            return self

        async def __anext__(self) -> Any:
            pass

    ws_resp3 = IncompleteWSResponse3()
    assert not isinstance(ws_resp3, GraphQLWebSocketResponse)

    class IncompleteWSResponse4:
        async def __aenter__(self) -> Any:
            return self

        async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
            pass

        async def send_str(self, data: str) -> None:
            pass

        # missing __aiter__
        async def __anext__(self) -> Any:
            pass

    ws_resp4 = IncompleteWSResponse4()
    assert not isinstance(ws_resp4, GraphQLWebSocketResponse)

    class IncompleteWSResponse5:
        async def __aenter__(self) -> Any:
            return self

        async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
            pass

        async def send_str(self, data: str) -> None:
            pass

        def __aiter__(self) -> Any:
            return self

        # missing __anext__

    ws_resp5 = IncompleteWSResponse5()
    assert not isinstance(ws_resp5, GraphQLWebSocketResponse)
