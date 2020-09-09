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
