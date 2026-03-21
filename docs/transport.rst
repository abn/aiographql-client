.. _transport:

Configuring Transport
=====================

The client allows you to customize how GraphQL requests are executed by using a transport abstraction.
By default, the client uses :class:`aiographql.client.transport.AiohttpTransport`.

Customizing Transport
*********************

You can provide a custom transport instance when creating the :class:`aiographql.client.GraphQLClient`.

.. code-block:: python

    from aiographql import GraphQLClient
    from aiographql.client.transport import AiohttpTransport

    transport = AiohttpTransport(endpoint="http://127.0.0.1:8080/v1/graphql")
    client = GraphQLClient(endpoint="http://127.0.0.1:8080/v1/graphql", transport=transport)

Custom HTTP Client Sessions
***************************

The :class:`aiographql.client.transport.AiohttpTransport` allows you to specify a `aiohttp Client Session <https://docs.aiohttp.org/en/stable/client_reference.html>`_
for use at various levels. Including per query and/or for all queries made by the client.

This can be done so by passing in the session when doing any of the following;

1. creating a client (this will be passed to the default `AiohttpTransport`)

.. code-block:: python

    aiographql.GraphQLClient(
        endpoint="http://127.0.0.1:8080/v1/graphql", session=session
    )

2. creating an `AiohttpTransport` explicitly

.. code-block:: python

    from aiographql.client.transport import AiohttpTransport

    transport = AiohttpTransport(
        endpoint="http://127.0.0.1:8080/v1/graphql", session=session
    )

3. making a query

.. code-block:: python

    await client.query(
        request=request, session=session
    )

3. creating a subscription

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
