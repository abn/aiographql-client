.. _introduction:

Getting started
===============

``aiographql-client`` is a modern, lightweight, and type-safe Python client for GraphQL, built on top of ``asyncio``, ``aiohttp``, and ``graphql-core``. It is designed for developers who value performance, flexibility, and a great developer experience.

Key Features
------------

* **Async-first**: Built from the ground up for ``asyncio``.
* **Multiple Transports**: Support for both ``aiohttp`` (default) and ``httpx``.
* **Subscriptions**: Built-in support for GraphQL subscriptions over WebSockets.
* **Type Safety**: Leverages ``graphql-core`` for query validation and ``Pydantic``/``dataclasses`` for data modeling.
* **Flexible Configuration**: Easily customize headers, timeouts, and connection pools.
* **Production Ready**: Used in high-performance production environments.

Quick Start
-----------

Getting started is as simple as passing your GraphQL query to :func:`aiographql.client.GraphQLClient.query`.

.. code-block:: python

    import asyncio
    from aiographql.client import GraphQLClient

    async def main():
        # Initialize the client
        client = GraphQLClient(
            endpoint="https://countries.trevorblades.com/",
        )

        # Execute a simple query
        response = await client.query("{ countries { name code } }")

        # Access data
        if not response.errors:
            for country in response.data["countries"][:5]:
                print(f"{country['name']} ({country['code']})")
        else:
            print(f"Errors: {response.errors}")

    if __name__ == "__main__":
        asyncio.run(main())

For more detailed examples on how to use the library, see :ref:`examples`.


.. hint:: The `JS GraphQL <https://plugins.jetbrains.com/plugin/8097-js-graphql>`_ plugin
    allows for easier working with GraphQL and also adds auto-complete during development.


Available Extras
~~~~~~~~~~~~~~~~

*   ``aiohttp``: Installs ``aiohttp`` for the default HTTP transport and WebSocket subscriptions.
*   ``httpx``: Installs ``httpx`` for the alternative HTTP transport and ``websockets`` for subscriptions.
*   ``pydantic``: Installs ``pydantic`` (v2) for enhanced data modeling and validation.

Installation
~~~~~~~~~~~~

.. tab-set::

   .. tab-item:: pip

      .. code-block:: shell

         pip install "aiographql-client[aiohttp,pydantic]"

   .. tab-item:: poetry

      .. code-block:: shell

         poetry add "aiographql-client[aiohttp,pydantic]"

.. _aiographql-client: https://pypi.org/project/aiographql-client/
.. _Poetry: https://python-poetry.org
