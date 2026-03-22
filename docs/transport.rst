.. _transport:

Configuring Transport
=====================

The client allows you to customize how GraphQL requests are executed by using a transport abstraction.
By default, the client automatically selects the best available transport based on installed packages.
If both ``aiohttp`` and ``httpx`` are installed, ``AiohttpTransport`` is preferred.

You can also explicitly specify a transport instance, such as :class:`aiographql.client.transport.AiohttpTransport` or :class:`aiographql.client.transport.HttpxTransport`.

Automatic Transport Selection
*****************************

If you do not provide a transport instance, the client will attempt to resolve a default one for you.
This is equivalent to passing ``transport=None``.

.. code-block:: python

    from aiographql import GraphQLClient

    # Automatically selects the best available transport
    client = GraphQLClient(endpoint="http://127.0.0.1:8080/v1/graphql")

Customizing Transport
*********************

You can provide a custom transport instance when creating the :class:`aiographql.client.GraphQLClient`.

.. code-block:: python

    from aiographql import GraphQLClient
    from aiographql.client.transport import AiohttpTransport

    transport = AiohttpTransport(endpoint="http://127.0.0.1:8080/v1/graphql")
    client = GraphQLClient(endpoint="http://127.0.0.1:8080/v1/graphql", transport=transport)

Using HttpxTransport
*********************

To use the `httpx` library for making requests, you can use :class:`aiographql.client.transport.HttpxTransport`.
This requires `httpx` to be installed.

.. code-block:: python

    from aiographql import GraphQLClient
    from aiographql.client.transport import HttpxTransport

    transport = HttpxTransport(endpoint="http://127.0.0.1:8080/v1/graphql")
    client = GraphQLClient(endpoint="http://127.0.0.1:8080/v1/graphql", transport=transport)

Custom HTTP Client Sessions
***************************

The :class:`aiographql.client.transport.AiohttpTransport` allows you to specify an `aiohttp Client Session <https://docs.aiohttp.org/en/stable/client_reference.html>`_
for use at various levels, including per query and for all queries made by the client.

Similarly, :class:`aiographql.client.transport.HttpxTransport` allows you to specify an `httpx.AsyncClient <https://www.python-httpx.org/async/>`_.

Providing your own session is highly recommended for **production use**, as it allows for better control over connection pooling, timeouts, and lifecycle management.

.. important::

    When providing your own session, the library will **not** automatically close it. You are responsible for ensuring the session is closed when it is no longer needed.

Usage Patterns
--------------

1. **Global Session (Recommended for high performance)**

   Creating a client with a pre-configured session:

.. code-block:: python

    import aiohttp
    from aiographql import GraphQLClient

    async with aiohttp.ClientSession(
        connector=aiohttp.TCPConnector(limit=200, force_close=True)
    ) as session:
        client = GraphQLClient(
            endpoint="http://127.0.0.1:8080/v1/graphql",
            session=session
        )
        await client.query("{ city { name } }")

2. **Per-query Session**

.. code-block:: python

    # Using Httpx
    async with httpx.AsyncClient() as async_client:
        await client.query(
            request=request,
            client=async_client
        )

Connection Limits & Subscriptions
*********************************

By default, the ``AiohttpTransport`` uses a ``TCPConnector`` with a connection limit of **100**.

Impact on Subscriptions
-----------------------

GraphQL subscriptions maintain a long-lived WebSocket connection. If you are using many concurrent subscriptions, you may reach the default connection limit.

*   **Exhausting limits**: If the limit is reached, subsequent requests (queries/mutations) may hang or time out until a connection is freed.
*   **Best Practice**: For production applications with high subscription counts or high concurrency, provide a custom session with an appropriate ``limit``:

.. code-block:: python

    import aiohttp

    # Increase limit for high-concurrency or many subscriptions
    connector = aiohttp.TCPConnector(limit=500)
    async with aiohttp.ClientSession(connector=connector) as session:
        client = GraphQLClient(endpoint="...", session=session)
        # Use client...

Reliable Production Use
***********************

For reliable production use, consider the following guides:

Timeouts
--------

Always set reasonable timeouts for your requests to prevent your application from hanging indefinitely.

.. code-block:: python

    import aiohttp

    timeout = aiohttp.ClientTimeout(total=30, connect=10)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        client = GraphQLClient(endpoint="...", session=session)
        # ...

Retries
-------

The library does not implement automatic retries. For production, consider using a library like `tenacity <https://tenacity.readthedocs.io/>`_ to handle transient network errors or rate limits.

.. code-block:: python

    from tenacity import retry, stop_after_attempt, wait_exponential

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def query_with_retry(client, request):
        return await client.query(request)

Behind SOCKS Proxies
********************

In order use via a socks proxy, you will need to custom connector, like the one provided by
`aiohttp-socks <https://pypi.org/project/aiohttp-socks/>`_.

Here is an example code snippet using this library.

.. code-block:: python

    connector = aiohttp_socks.ProxyConnector(
        proxy_type=aiohttp_socks.ProxyType.SOCKS5,
        host="127.0.0.1",
        port=1080,
        rdns=True,
    )
    async with aiohttp.ClientSession(connector=connector) as session:
        client = GraphQLClient(
            endpoint="http://gql.example.com/v1/graphql", session=session
        )
        await client.query(request="query { city { name } }")
