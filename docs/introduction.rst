.. _introduction:

Getting started
===============

This package is intended to be used as a client library for when your application requires
interacting with a GraphQL server.

Getting started is as simple as passing your GraphQL query to :func:`aiographql.client.GraphQLClient.query`.

.. code-block:: python

        async def get_logged_in_username(token: str) -> GraphQLResponse:
            client = GraphQLClient(
                endpoint="https://api.github.com/graphql",
                headers={"Authorization": f"Bearer {token}"},
            )
            return await client.query("query { viewer { login } }")


For more detailed examples on how to use the library, see :ref:`examples`.


.. hint:: The `JS GraphQL <https://plugins.jetbrains.com/plugin/8097-js-graphql>`_ plugin
    allows for easier working with GraphQL and also adds auto-complete during development.


Adding to your project
----------------------

You can add the the package to your project by specifying a dependency to `aiographql-client`_.

If you are using `Poetry`_ to manage your project, the following command should do the trick.

To install with the default `aiohttp` transport:

.. code-block:: shell

    poetry add aiographql-client[aiohttp]

To use `httpx` as the transport:

.. code-block:: shell

    poetry add aiographql-client[httpx]

To use `websockets` for subscriptions (alternative to `aiohttp`):

.. code-block:: shell

    poetry add aiographql-client[websockets]

When using pip you can do the following.

.. code-block:: shell

    pip install aiographql-client[aiohttp]

.. _aiographql-client: https://pypi.org/project/aiographql-client/
.. _Poetry: https://python-poetry.org
