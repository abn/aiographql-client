.. _query_subscriptions:

Subscriptions
-------------
The following example makes use of the `Hasura World Database Demo <https://github.com/twyla-ai/hasura-world-db>`_
application as there aren't many public GraphQL schema that allow subscriptions for testing. You can
use the project's provided docker compose file to start an instance locally.

By default the subscription is closed if any of the following event type is received.
    1. :attr:`aiographql.client.GraphQLSubscriptionEventType.ERROR`
    2. :attr:`aiographql.client.GraphQLSubscriptionEventType.CONNECTION_ERROR`
    3. :attr:`aiographql.client.GraphQLSubscriptionEventType.COMPLETE`

The following example will subscribe to any change events and print the event as is to
stdout when either :attr:`aiographql.client.GraphQLSubscriptionEventType.DATA` or
:attr:`aiographql.client.GraphQLSubscriptionEventType.ERROR` is received.

.. code-block:: python

    request = GraphQLRequest(
        query="""
        subscription {
          city(where: {name: {_eq: "Berlin"}}) {
            name
            id
          }
        }
    """
    )
    # subscribe to data and error events, and print them
    subscription = await client.subscribe(
        request=request, on_data=print, on_error=print
    )
    # unsubscribe
    await subscription.unsubscribe_and_wait()

.. hint:: By default, subscriptions negotiate the modern standard :code:`"graphql-transport-ws"`
    sub-protocol and fall back to legacy :code:`"graphql-ws"`. In the case you want to restrict
    the GraphQL over WebSocket sub-protocol to use, you may do so by setting
    :attr:`aiographql.client.GraphQLSubscription.protocols`.
    For example, :code:`await client.subscribe(..., protocols="graphql-transport-ws")` or
    :code:`await client.subscribe(..., protocols="graphql-ws")`.

    Similarly, if your server requires additional fields in the `connection_init` payload
    (for example, an `authToken` or `headers`), you can provide them using the
    `connection_init_payload` parameter.

    .. code-block:: python

        subscription = await client.subscribe(
            request=request,
            connection_init_payload={
                "authToken": "my-secret-token",
                "headers": {"X-Custom-Auth": "value"}
            }
        )

    Note that headers provided in the `GraphQLRequest` will be merged with and take
    precedence over headers in `connection_init_payload`.

Callback Registry
*****************

Subscriptions make use of :class:`cafeteria.asyncio.callbacks.CallbackRegistry` internally to
trigger registered callbacks when an event of a particular type is encountered. You can
also register a *Coroutine* if required.

.. code-block:: python

    # both the following statements have the same effect
    subscription = await client.subscribe(
        request=request, on_data=print, on_error=print
    )
    subscription = await client.subscribe(
        request=request, callbacks={
            GraphQLSubscriptionEventType.DATA: print,
            GraphQLSubscriptionEventType.ERROR: print,
        }
    )

    # this can also be done as below
    registry = CallbackRegistry()
    registry.register(GraphQLSubscriptionEventType.DATA, print)
    registry.register(GraphQLSubscriptionEventType.ERROR, print)

If you'd like a single callback for all event types or any "unregistered" event, you can
simply set the event type to `None` when registering the callback.

>>> registry.register(None, print)

Here is an example that will print the timestamp every time a keep-alive event is received.

.. code-block:: python

    subscription.callbacks.register(
        GraphQLSubscriptionEventType.KEEP_ALIVE,
        lambda x: print(f"Received keep-alive at {datetime.utcnow().isoformat()}")
    )

Waiting for Subscriptions
*************************

By default, :meth:`aiographql.client.GraphQLClient.subscribe` returns a :class:`aiographql.client.subscription.GraphQLSubscription` object immediately, while the subscription runs in the background.

If you want to wait for the subscription to complete (e.g., in a simple script), you can pass ``wait=True``.

.. code-block:: python

    await client.subscribe(request=request, on_data=print, wait=True)

Alternatively, you can wait for the background task manually:

.. code-block:: python

    subscription = await client.subscribe(request=request, on_data=print)
    # Do other things...
    await subscription.task

Error Handling in Subscriptions
*******************************

When a subscription encounters an error, the ``on_error`` callback is triggered. It's important to note that by default, most errors will cause the subscription to close.

.. code-block:: python

    async def handle_error(error):
        print(f"Subscription error: {error}")
        # Logic to potentially restart subscription if needed

    subscription = await client.subscribe(
        request=request,
        on_data=print,
        on_error=handle_error
    )

Connection Pool Limits
**********************

As mentioned in the :ref:`transport` section, the default connection limit is 100. Each active subscription consumes one connection from this pool. If you anticipate having many concurrent subscriptions, ensure your session's connector is configured with a higher limit.
