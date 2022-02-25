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

.. hint:: In the case you want to specify the GraphQL over WebSocket sub-protocol to use,
    you may do so by setting :attr:`aiographql.client.GraphQLSubscription.protocols`.
    For example, :code:`await client.subscribe(..., protocols="graphql-ws")`. This is
    required for certain server implementations like `Apollo Server <https://www.apollographql.com/docs/apollo-server/>`_
    as it supports multiple implementations.

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
