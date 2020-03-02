Usage Examples
==============
Many of the following examples make use of `GitHub GrpahQL API <https://developer.github.com/v4/>`_.
You can retrieve a token as detailed `here <https://developer.github.com/v4/guides/forming-calls/#authenticating-with-graphql>`_.

Simple Query
------------
The :class:`aiographql.client.GraphQLClient` can be used to store headers like *Authorization* that need to be sent with
every request made.

.. code-block:: python

    client = GraphQLClient(
        endpoint="https://api.github.com/graphql",
        headers={"Authorization": f"Bearer {TOKEN}"},
    )
    request = GraphQLRequest(
        query="""
            query {
              viewer {
                login
              }
            }
        """
    )
    response = await client.query(request=request)

If you have a valid token, the above query will return the following data.

>>> response.data
{'viewer': {'login': 'username'}}

If you intend to only make use of the query once, ie. it is not re-used, you may forgo
the creation of an :class:`aiographql.client.GraphQLRequest` instance and pass in the
query string direct to :meth:`aiographql.client.GraphQLClient.query`.

.. code-block:: python

    await client.query(request="{ viewer { login } }")

Client Side Query Validation
----------------------------
Because we make use of `GraphQL Core 3 <https://github.com/graphql-python/graphql-core-next>`_, client-side
query validation is performed by default.

.. code-block:: python

    request = GraphQLRequest(
        query="""
            query {
              bad {
                login
              }
            }
        """
    )
    response: GraphQLResponse = await client.query(request=request)


This will raise :class:`aiographql.client.GraphQLClientValidationException`. The message
will also contain information about the error.

.. code-block:: python

    aiographql.client.exceptions.GraphQLClientValidationException: Query validation failed

    Cannot query field 'bad' on type 'Query'.

    GraphQL request:3:15
    2 |             query {
    3 |               bad {
      |               ^
    4 |                 login

    Process finished with exit code 1


Server Side Query Validation
----------------------------
You can skip the client side validation, forcing server side validation instead by setting
the :attr:`aiographql.client.GraphQLRequest.validate` to `False` before making the request.

.. code-block:: python

    request = GraphQLRequest(
        query="""
            query {
              bad {
                login
              }
            }
        """,
        validate=False
    )
    response: GraphQLResponse = await client.query(request=request)

>>> response.data
{}
>>> response.errors
[GraphQLError(extensions={'code': 'undefinedField', 'typeName': 'Query', 'fieldName': 'bad'}, locations=[{'line': 3, 'column': 15}], message="Field 'bad' doesn't exist on type 'Query'", path=['query', 'bad'])]

Query Variables
---------------

.. code-block:: python

    request = GraphQLRequest(
        query="""
            query($number_of_repos:Int!) {
              viewer {
                 repositories(last: $number_of_repos) {
                   nodes {
                     name
                     isFork
                   }
                 }
               }
            }
        """,
        variables={"number_of_repos": 3},
    )
    response: GraphQLResponse = await client.query(request=request)

You can override default values specified in the prepared request too. The values are
upserted into the existing defaults.

.. code-block:: python

    response: GraphQLResponse = await client.query(request=request, variables={
        "number_of_repos": 1
    })

Specifying Operation Name
-------------------------
You can use a single :class:`aiographql.client.GraphQLRequest` object to stop a query
wit multiple operations.

.. code-block:: python

    request = GraphQLRequest(
        query="""
            query FindFirstIssue {
              repository(owner:"octocat", name:"Hello-World") {
                issues(first:1) {
                  nodes {
                    id
                    url
                  }
                }
              }
            }

            query FindLastIssue {
              repository(owner:"octocat", name:"Hello-World") {
                issues(last:1) {
                  nodes {
                    id
                    url
                  }
                }
              }
            }
        """,
        operation="FindFirstIssue",
    )

    # use the default operation (FindFirstIssue)
    response = await client.query(request=request)

    # use the operation FindLastIssue
    response = await client.query(
        request=request,
        operation="FindLastIssue"
    )

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
