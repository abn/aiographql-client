.. _errors:

Errors and Exceptions
=====================

``aiographql-client`` distinguishes between two layers of failure:

* **Exceptions** raised by the client when a request cannot be completed:
  validation failed, transport broke, server returned a non-2XX response,
  introspection failed, or codec failed.
* **GraphQL errors** returned by the server *in* a successful HTTP response.
  These do not raise. They are on
  :attr:`GraphQLResponse.errors <aiographql.client.GraphQLResponse.errors>`
  alongside any partial data.

Exception Hierarchy
-------------------

Every exception raised by the client derives from
:class:`~aiographql.client.GraphQLClientException`.

.. list-table::
   :widths: 30 25 45
   :header-rows: 1

   * - Exception
     - Raised by
     - Trigger
   * - :class:`~aiographql.client.GraphQLClientValidationException`
     - :meth:`~aiographql.client.GraphQLClient.query`,
       :meth:`~aiographql.client.GraphQLClient.validate`
     - Client-side validation against the introspected schema failed.
   * - :class:`~aiographql.client.GraphQLRequestException`
     - :meth:`~aiographql.client.GraphQLClient.query`
     - The server responded with a non-2XX status. The originating response is
       attached as ``.response``.
   * - ``GraphQLTransportException``
     - Any transport call
     - HTTP, TCP, TLS, or WebSocket failure. Subclass of
       :class:`~aiographql.client.GraphQLClientException`; imported from
       ``aiographql.client.exceptions``.
   * - :class:`~aiographql.client.GraphQLIntrospectionException`
     - :meth:`~aiographql.client.GraphQLClient.introspect`,
       :meth:`~aiographql.client.GraphQLClient.get_schema`
     - The endpoint refused introspection or returned an unusable schema.
   * - :class:`~aiographql.client.GraphQLCodecException`
     - Codec encode/decode
     - Variable encoding or response decoding failed for the configured codec.

Pre-flight Validation
---------------------

When ``validate=True`` (the default on both
:class:`~aiographql.client.GraphQLClient` and
:class:`~aiographql.client.GraphQLRequest`), the client introspects the schema
and validates the query before sending it. A query that fails validation is
not sent to the server.

.. code-block:: python

    from aiographql.client import (
        GraphQLClient,
        GraphQLClientValidationException,
    )

    client = GraphQLClient(endpoint="https://api.example.com/graphql")

    try:
        await client.query("{ doesNotExist { id } }")
    except GraphQLClientValidationException as exc:
        # exc.args[0] is a multi-line summary of every validation error.
        log.warning("Bad query: %s", exc)

To skip validation (for example, when the server has introspection disabled),
set ``validate=False`` on the request or on the client:

.. code-block:: python

    # Skip for one request:
    request = GraphQLRequest(query="...", validate=False)

    # Skip for the whole client:
    client = GraphQLClient(endpoint="...", validate=False)

Transport and HTTP Errors
-------------------------

Network-layer failures raise ``GraphQLTransportException``. HTTP responses
outside the 2XX range raise
:class:`~aiographql.client.GraphQLRequestException` with the full response
attached so the body and status can be inspected:

.. code-block:: python

    from aiographql.client import GraphQLRequestException
    from aiographql.client.exceptions import GraphQLTransportException

    try:
        response = await client.query(request)
    except GraphQLRequestException as exc:
        # Non-2XX. The server's response is attached.
        log.error("HTTP %s: %s", exc.response.json, exc)
    except GraphQLTransportException as exc:
        # DNS, TCP, TLS, WebSocket, etc.
        log.error("Transport failure: %s", exc)

For retry strategies around these exceptions, see :ref:`production`.

GraphQL Errors in a Successful Response
---------------------------------------

The GraphQL specification permits a server to return HTTP 200 with both
``data`` and ``errors``. A successful HTTP call returns a
:class:`~aiographql.client.GraphQLResponse` and any server-reported errors
are on ``response.errors``.

.. code-block:: python

    response = await client.query(request)

    if response.errors:
        for error in response.errors:
            log.warning(
                "GraphQL error at %s: %s",
                ".".join(map(str, error.path or [])),
                error.message,
            )

    # Partial data is still available even when there are errors.
    if response.data:
        process(response.data)

Each entry is a :class:`~aiographql.client.GraphQLError` carrying ``message``,
``path``, ``locations``, and any server-specific ``extensions``. Unknown
fields on the error object are preserved on a dynamically constructed
subclass.

Introspection and Codec Errors
------------------------------

:class:`~aiographql.client.GraphQLIntrospectionException` is raised when the
client cannot build a schema from the endpoint, typically because
introspection is disabled or the endpoint returned an error in response to
the introspection query. The exception message includes the GraphQL errors
that prevented schema construction.

:class:`~aiographql.client.GraphQLCodecException` is raised by a configured
:class:`~aiographql.client.GraphQLCodec` when encoding request variables or
decoding response data fails. The default codec raises this only for
unrecoverable type mismatches; custom codecs may use it more liberally.

Choosing a Handling Strategy
----------------------------

* **Validation errors** are programmer errors. Surface them in tests and CI.
  Do not retry them.
* **Transport and HTTP 5XX** are transient. Retry with backoff
  (see :ref:`production`).
* **HTTP 4XX** are caller errors (authentication, rate limit). Surface to the
  user; do not retry blindly.
* **GraphQL errors in a 200 response** are domain errors. Inspect ``path``
  and ``extensions`` to route them. Partial ``data`` may still be useful.
* **Introspection errors** mean the schema is unavailable. Either set
  ``validate=False`` and accept the loss of pre-flight checks, or fail fast
  at startup.
