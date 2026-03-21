.. _transport:

Configuring Transport
=====================

The client allows you to customize how GraphQL requests are executed by using a transport abstraction.
By default, the client uses :class:`aiographql.client.transport.AiohttpTransport`.
It also supports :class:`aiographql.client.transport.HttpxTransport` for using the `httpx` library.

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

The :class:`aiographql.client.transport.AiohttpTransport` allows you to specify a `aiohttp Client Session <https://docs.aiohttp.org/en/stable/client_reference.html>`_
for use at various levels. Including per query and/or for all queries made by the client.

Similarly, :class:`aiographql.client.transport.HttpxTransport` allows you to specify a `httpx.AsyncClient <https://www.python-httpx.org/async/>`_.

This can be done so by passing in the session/client when doing any of the following;

1. creating a client (this will be passed to the default `AiohttpTransport` or provided transport)

.. code-block:: python

    # For Aiohttp
    aiographql.GraphQLClient(
        endpoint="http://127.0.0.1:8080/v1/graphql", session=session
    )

    # For Httpx
    from aiographql.client.transport import HttpxTransport
    transport = HttpxTransport(endpoint="...", client=async_client)
    aiographql.GraphQLClient(
        endpoint="http://127.0.0.1:8080/v1/graphql", transport=transport
    )

2. creating a transport explicitly

.. code-block:: python

    # Aiohttp
    from aiographql.client.transport import AiohttpTransport

    transport = AiohttpTransport(
        endpoint="http://127.0.0.1:8080/v1/graphql", session=session
    )

    # Httpx
    from aiographql.client.transport import HttpxTransport

    transport = HttpxTransport(
        endpoint="http://127.0.0.1:8080/v1/graphql", client=async_client
    )

3. making a query

.. code-block:: python

    # Aiohttp
    await client.query(
        request=request, session=session
    )

    # Httpx
    await client.query(
        request=request, client=async_client
    )

3. creating a subscription

Note: Subscriptions are currently only supported via `AiohttpTransport`.

.. code-block:: python

    await client.subscribe(
        request=request, session=session
    )

Using Behind SOCK Proxies
*************************

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
