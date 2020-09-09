.. _query_validation:

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
