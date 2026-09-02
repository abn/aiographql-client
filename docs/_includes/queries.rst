.. _query:

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

Mutations
---------

Mutations are performed using the same :meth:`aiographql.client.GraphQLClient.query` method, as the GraphQL specification treats them similarly to queries but with side effects.

.. code-block:: python

    request = GraphQLRequest(
        query="""
            mutation AddStar($starrableId: ID!) {
              addStar(input: {starrableId: $starrableId}) {
                starrable {
                  stargazerCount
                }
              }
            }
        """,
        variables={"starrableId": "R_kgDOJ-..."}
    )
    response = await client.query(request)

Alternatively, you can use the :meth:`aiographql.client.GraphQLClient.post` method to explicitly use a POST request (which is the default for ``query`` anyway).

.. code-block:: python

    response = await client.post(request)

Custom Headers per Request
--------------------------

You can provide custom headers for a specific request. These will be merged with the headers configured on the client.

.. code-block:: python

    response = await client.query(
        request="{ viewer { login } }",
        headers={"X-Custom-Header": "value"}
    )

Query Extensions
----------------

You can pass GraphQL extensions along with your queries. Extensions are extra information sent to the server that may be used for features like persisted queries, caching hints, or custom server behavior.

.. code-block:: python

    request = GraphQLRequest(
        query="{ viewer { login } }",
        extensions={"persistedQuery": {"version": 1, "sha256Hash": "..."}}
    )
    response = await client.query(request=request)

Like variables and operation names, you can override the default extensions when making the request:

.. code-block:: python

    response = await client.query(
        request=request,
        extensions={"customExtension": "value"}
    )

Handling Errors
---------------

Always check for errors in the response. The :class:`aiographql.client.GraphQLResponse` object contains an ``errors`` attribute which is a list of errors returned by the server.

.. code-block:: python

    response = await client.query("{ viewer { nonExistentField } }")
    if response.errors:
        for error in response.errors:
            print(f"Error: {error['message']}")
            # Access extensions, locations, path if available
            print(f"Code: {error.get('extensions', {}).get('code')}")
    else:
        print(response.data)
