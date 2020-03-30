# Asynchronous GraphQL Client
[![PyPI version](https://badge.fury.io/py/aiographql-client.svg)](https://badge.fury.io/py/aiographql-client)
[![Python Versions](https://img.shields.io/pypi/pyversions/aiographql-client)](https://pypi.org/project/aiographql-client/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Documentation Status](https://readthedocs.org/projects/aiographql-client/badge/?version=latest)](https://aiographql-client.readthedocs.io/en/latest/?badge=latest)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Sonarcloud Status](https://sonarcloud.io/api/project_badges/measure?project=twyla-ai_aiographql-client&metric=alert_status)](https://sonarcloud.io/dashboard?id=twyla-ai_aiographql-client)
[![](https://github.com/twyla-ai/aiographql-client/workflows/Test%20Suite/badge.svg)](https://github.com/twyla-ai/aiographql-client/actions?query=workflow%3A%22Test+Suite%22)

An asynchronous GraphQL client built on top of aiohttp and graphql-core-next. The client by default introspects schemas and validates all queries prior to dispatching to the server.

## Documentation

For the most recent project documentation, you can visit https://aiographql-client.readthedocs.io/.

## Installation
`pip install aiographql-client`

## Example Usage
Here are some example usages of this client implementation. For more examples, and advanced scenarios, 
see [Usage Examples](https://aiographql-client.readthedocs.io/en/latest/examples.html) section in 
the documentation.

### Simple Query
```py
async def get_logged_in_username(token: str) -> GraphQLResponse:
    client = GraphQLClient(
        endpoint="https://api.github.com/graphql",
        headers={"Authorization": f"Bearer {token}"},
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
    return await client.query(request=request)
```

```console
>>> import asyncio
>>> response = asyncio.run(get_logged_in_username("<TOKEN FROM GITHUB GRAPHQL API>"))
>>> response.data
{'viewer': {'login': 'username'}}
```

### Query Subscription
```py
async def print_city_updates(client: GraphQLClient, city: str) -> None:
    request = GraphQLRequest(
        query="""
            subscription ($city:String!) {
              city(where: {name: {_eq: $city}}) {
                description
                id
              }
            }
        """,
        variables={"city": city},
    )
    # subscribe to data and error events, and print them
    await client.subscribe(
        request=request, on_data=print, on_error=print, wait=True
    )
```

For custom event specific callback registration, see [Callback Registry Documentation](https://aiographql-client.readthedocs.io/en/latest/examples.html#callback-registry).

### Query Validation Failures
If your query is invalid, thanks to graphql-core-next, we get a detailed exception in the traceback.

```
aiographql.client.exceptions.GraphQLClientValidationException: Query validation failed

Cannot query field 'ids' on type 'chatbot'. Did you mean 'id'?

GraphQL request (4:13)
3:           chatbot {
4:             ids, bot_names
               ^
5:           }

Cannot query field 'bot_names' on type 'chatbot'. Did you mean 'bot_name' or 'bot_language'?

GraphQL request (4:18)
3:           chatbot {
4:             ids, bot_names
                    ^
5:           }

```

### Query Variables & Operations
Support for multi-operation requests and variables is available via the client. For example,
the following request contains multiple operations. The instance specifies default values to use.

```py
request = GraphQLRequest(
    query="""
    query get_bot_created($id: Int) {
      chatbot(where: {id: {_eq: $id}}) {
        id, created
      }
    }
    query get_bot_name($id: Int) {
      chatbot(where: {id: {_eq: $id}}) {
        id, bot_name
      }
    }
    """,
    variables={"id": 109},
    operation="get_bot_name"
)
```

The default values can be overridden at the time of making the request if required. 

```py
await client.query(request=request, variables={"id": 20}, operation="get_bot_created")
```
