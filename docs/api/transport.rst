.. _api_transport:

Transport
=========

GraphQLTransport
----------------
.. autoclass:: aiographql.client.transport.base.GraphQLTransport
    :members:

AiohttpTransport
----------------
.. autoclass:: aiographql.client.transport.aiohttp.AiohttpTransport
    :members:

HttpxTransport
--------------
.. autoclass:: aiographql.client.transport.httpx.HttpxTransport
    :members:

AiohttpSubscriptionTransport
----------------------------
.. autoclass:: aiographql.client.transport.aiohttp.AiohttpSubscriptionTransport
    :members:

WebsocketSubscriptionTransport
------------------------------
.. autoclass:: aiographql.client.transport.websocket.WebsocketSubscriptionTransport
    :members:

GraphQLWebSocketResponse
------------------------
.. autoclass:: aiographql.client.transport.base.GraphQLWebSocketResponse
    :members:

get_default_transport
---------------------
.. autofunction:: aiographql.client.transport.get_default_transport

get_default_subscription_transport
----------------------------------
.. autofunction:: aiographql.client.transport.get_default_subscription_transport
