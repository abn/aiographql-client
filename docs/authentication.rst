.. _authentication:

Authentication
==============

GraphQL servers vary in how they expect authentication. This page covers the
patterns supported by :class:`aiographql.client.GraphQLClient` and the layer
each one belongs to.

Headers are layered in the following order of precedence (least to greatest):

1. Client-default headers passed to
   :class:`~aiographql.client.GraphQLClient` at construction.
2. Per-request headers on :class:`~aiographql.client.GraphQLRequest`.
3. Headers passed to :meth:`~aiographql.client.GraphQLClient.query` itself.

A later layer overrides the same header from an earlier one.

Bearer Tokens
-------------

The common case. Set ``Authorization`` once on the client, reuse it for every
request:

.. code-block:: python

    client = GraphQLClient(
        endpoint="https://api.github.com/graphql",
        headers={"Authorization": f"Bearer {token}"},
    )
    response = await client.query("{ viewer { login } }")

Basic Authentication
--------------------

Standard HTTP basic auth fits the same shape. Encode ``user:password`` as
Base64 and set ``Authorization``:

.. code-block:: python

    import base64

    credentials = base64.b64encode(f"{user}:{password}".encode()).decode()
    client = GraphQLClient(
        endpoint="https://api.example.com/graphql",
        headers={"Authorization": f"Basic {credentials}"},
    )

Per-request Override
--------------------

To call a service with multiple identities (for example, an admin client that
sometimes acts on behalf of a user), override the header per request without
constructing a new client:

.. code-block:: python

    response = await client.query(
        request="{ me { id } }",
        headers={"Authorization": f"Bearer {user_token}"},
    )

The same pattern is the right place for one-off headers such as
``X-Request-Id`` or feature flags.

Refreshing Short-lived Tokens
-----------------------------

Bearer tokens that expire need to be refreshed before each request. The
client does not provide a refresh hook; instead, hold the refresh logic in a
helper that returns a fresh token, and pass it via the per-request ``headers``
argument:

.. code-block:: python

    async def authorized_query(client, request, token_source):
        token = await token_source.get_valid_token()
        return await client.query(
            request=request,
            headers={"Authorization": f"Bearer {token}"},
        )

For long-lived clients that own their token state, cache the token on the
helper and only refresh when expiry is close:

.. code-block:: python

    import time

    class TokenSource:
        def __init__(self, fetch):
            self._fetch = fetch
            self._token: str | None = None
            self._expires_at: float = 0.0

        async def get_valid_token(self) -> str:
            if self._token is None or time.monotonic() > self._expires_at - 30:
                token, ttl = await self._fetch()
                self._token = token
                self._expires_at = time.monotonic() + ttl
            return self._token

Cookies and Session-based Auth
------------------------------

Servers that authenticate via cookies (Django, Rails, set-cookie flows) need
a transport session that persists cookies across requests. Pass a managed
``aiohttp.ClientSession`` or ``httpx.AsyncClient`` and the cookie jar is
reused for every call:

.. code-block:: python

    import aiohttp
    from aiographql.client import GraphQLClient

    async with aiohttp.ClientSession() as session:
        # Log in once. The session keeps the cookies.
        await session.post(
            "https://api.example.com/login",
            json={"user": user, "password": password},
        )

        client = GraphQLClient(
            endpoint="https://api.example.com/graphql",
            session=session,
        )
        response = await client.query("{ me { id } }")

The same approach works with ``httpx.AsyncClient`` if the project uses the
``httpx`` extra.

API Keys in Custom Headers
--------------------------

Some servers expect the key in a non-``Authorization`` header. There is no
special API for this; treat it like any other default header:

.. code-block:: python

    client = GraphQLClient(
        endpoint="https://api.example.com/graphql",
        headers={"X-API-Key": api_key},
    )

Subscriptions
-------------

WebSocket subscriptions follow the ``graphql-ws`` protocol, which sends the
auth payload during the ``connection_init`` step. The headers configured on
the client and request are forwarded into that payload by the subscription
transport, so the same Bearer / API key patterns above apply.

For a server that requires a custom ``connectionParams`` shape, set the
matching keys via request headers; the subscription transport passes them
through unchanged.
