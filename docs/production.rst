.. _production:

Production Guide
================

This guide collects the operational concerns that come up when running
``aiographql-client`` in a long-lived service: session lifecycle, connection
pool sizing, timeouts, retries, observability, and shutdown.

Sections build on :ref:`transport`, :ref:`authentication`, and :ref:`errors`;
each one is referenced where relevant rather than restated.

Session Lifecycle
-----------------

For any process that handles more than a handful of requests, provide your
own transport session and reuse it across the lifetime of the client. The
client does not close sessions it did not create; ownership stays with the
caller.

The recommended shape is an application-scoped session bound to the
application lifecycle (FastAPI startup/shutdown, ``asyncio.run`` entry
function, ``contextlib.AsyncExitStack``, etc.):

.. code-block:: python

    import aiohttp
    from aiographql.client import GraphQLClient

    async def main():
        async with aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(limit=200),
        ) as session:
            client = GraphQLClient(
                endpoint="https://api.example.com/graphql",
                session=session,
            )
            await run_application(client)
        # Session closes here; in-flight requests are aborted.

For ``httpx``:

.. code-block:: python

    import httpx
    from aiographql.client import GraphQLClient

    async with httpx.AsyncClient(
        limits=httpx.Limits(max_connections=200, max_keepalive_connections=50),
    ) as session:
        client = GraphQLClient(
            endpoint="https://api.example.com/graphql",
            session=session,
        )
        await run_application(client)

Connection Pool Sizing
----------------------

The default ``aiohttp`` connector limit is 100. Two patterns push past it:

* High request concurrency. Size the pool above your steady-state request
  fan-out, leaving headroom for retries.
* Subscriptions. Each subscription holds an open WebSocket for its lifetime
  and counts against the pool. Add the expected concurrent subscription
  count to the request fan-out estimate.

Set the limit on the connector for ``aiohttp`` or on ``Limits`` for
``httpx``. Going too low causes new requests to queue; going too high wastes
file descriptors and lets a stalled backend retain more in-flight work.

Timeouts
--------

The library does not impose timeouts. Configure them on the session:

.. code-block:: python

    timeout = aiohttp.ClientTimeout(total=30, connect=5, sock_read=10)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        ...

For ``httpx``:

.. code-block:: python

    timeout = httpx.Timeout(30.0, connect=5.0, read=10.0)
    async with httpx.AsyncClient(timeout=timeout) as session:
        ...

A ``total`` timeout caps end-to-end latency for a request. ``connect`` and
``read`` (or ``sock_read``) catch unresponsive peers without waiting out the
full budget. Pick values that match the slowest acceptable user-facing
latency for the operation.

Retries
-------

The client does not retry. Wrap calls with ``tenacity`` (or any retry
library) and limit retries to transient failures only: connection errors,
timeouts, and HTTP 5XX. Do not retry validation errors or 4XX responses.

.. code-block:: python

    from tenacity import (
        retry,
        retry_if_exception_type,
        stop_after_attempt,
        wait_exponential,
    )
    from aiographql.client import GraphQLRequestException
    from aiographql.client.exceptions import GraphQLTransportException

    @retry(
        retry=retry_if_exception_type((GraphQLTransportException, asyncio.TimeoutError)),
        wait=wait_exponential(multiplier=0.5, min=0.5, max=8),
        stop=stop_after_attempt(4),
        reraise=True,
    )
    async def query_with_retry(client, request):
        return await client.query(request)

For HTTP 5XX-specific retries, catch
:class:`~aiographql.client.GraphQLRequestException` and inspect
``exc.response.json`` to decide whether to retry.

Schema Validation
-----------------

Pre-flight validation catches programmer errors before they hit the network,
but it requires introspection on the server.

* **Development:** keep ``validate=True``. Bad queries fail fast with a clear
  message.
* **Production with introspection disabled:** set ``validate=False`` on the
  client. Surface server-side validation as
  :class:`~aiographql.client.GraphQLRequestException` or via
  ``response.errors``.
* **Production with introspection enabled:** consider setting
  ``schema_ttl`` on the client so the introspected schema refreshes
  periodically without restarting the service.

See :ref:`errors` for handling each layer.

Observability
-------------

Logging and tracing belong on the transport session, not on the GraphQL
client. Use ``aiohttp``'s :py:class:`~aiohttp.TraceConfig` or
``httpx``'s event hooks to capture request/response metadata for every call,
including ones that fail before the GraphQL layer sees them.

Minimal ``aiohttp`` example:

.. code-block:: python

    import logging
    import aiohttp

    log = logging.getLogger("graphql")

    async def on_request_start(session, ctx, params):
        ctx.start = asyncio.get_running_loop().time()

    async def on_request_end(session, ctx, params):
        elapsed = asyncio.get_running_loop().time() - ctx.start
        log.info(
            "graphql %s %s %.3fs",
            params.method,
            params.url,
            elapsed,
        )

    trace_config = aiohttp.TraceConfig()
    trace_config.on_request_start.append(on_request_start)
    trace_config.on_request_end.append(on_request_end)

    async with aiohttp.ClientSession(trace_configs=[trace_config]) as session:
        client = GraphQLClient(endpoint="...", session=session)

For tracing, install an OpenTelemetry instrumentation for the underlying
transport (``opentelemetry-instrumentation-aiohttp-client`` or
``opentelemetry-instrumentation-httpx``); spans cover every call the client
makes.

Graceful Shutdown
-----------------

The client itself is cheap to construct and discard. The expensive part is
the session. On shutdown:

1. Stop accepting new work that would call the client.
2. Cancel or drain any subscriptions
   (:meth:`GraphQLSubscription.unsubscribe
   <aiographql.client.GraphQLSubscription.unsubscribe>`).
3. Await in-flight queries with a deadline.
4. Exit the ``async with`` block (or call ``await session.close()``) so the
   transport closes its connector and releases file descriptors.

Skipping step 4 in long-running services leaks connections; in
short-running scripts it leaks them only on process exit but produces
``Unclosed client session`` warnings.

Health Checks
-------------

A liveness probe should not call the upstream GraphQL endpoint. A readiness
probe can, but should issue a minimal query (often ``{ __typename }``) and
treat any
:class:`~aiographql.client.GraphQLClientException` subclass as
"not ready" without bringing the pod down.

.. code-block:: python

    async def graphql_ready(client) -> bool:
        try:
            await asyncio.wait_for(
                client.query("{ __typename }"),
                timeout=2,
            )
        except Exception:
            return False
        return True
