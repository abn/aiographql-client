.. _transport:

Configuring HTTP Transport
==========================

Custom HTTP Client Sessions
***************************

The client allows you to specify a `aiohttp Client Session <https://docs.aiohttp.org/en/stable/client_reference.html>`_
for use at various levels. Including per query and/or for all queries made by the client.

This can be done so by passing in the session when doing any of the following;

1. creating a client

.. code-block:: python

    aiographql.GraphQLClient(
        endpoint="http://127.0.0.1:8080/v1/graphql", session=session
    )

2. making a query

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
