# Asyncio GraphQL Client
An asyncio GraphQL client built on top of aiohttp and graphql-core-next. The client by default introspects schemas and validates all queries prior to dispatching to the server.

## Installation
`pip install aiographql-client`

## Example Usage
Here are some example usages of this client implementation. These examples use the [Hasura GraphQL Engine](https://hasura.io/).

### Simple Query
```py
async def get_bots():
    client = GraphQLClient(
        endpoint="http://localhost:8080/v1alpha1/graphql",
        headers={"x-hasura-admin-secret": "myadminsecretkey"},
    )
    request = GraphQLRequest(
        query="""
        query get_bots {
          chatbot {
            id, bot_name
          }
        }
        """
    )
    transaction = await client.post(request)

    # display the query used
    print(transaction.request.query)

    # dump the response data
    print(transaction.response.data)
```

### Query Subscription
```py
async def get_bots():
    client = GraphQLClient(
        endpoint="http://localhost:8080/v1alpha1/graphql",
        headers={"x-hasura-admin-secret": "myadminsecretkey"},
    )
    request = GraphQLRequest(
        query="""
        subscription get_bot_updates {
          chatbot {
            id, bot_name
          }
        }
        """
    )
    
    # configure callbacks, here we simply print the event message when a data event
    # (`GraphQLSubscriptionEvent`) is received.
    callbacks = CallbackRegistry()
    callbacks.register(
        GraphQLSubscriptionEventType.DATA, lambda event: print(event.message)
    )
    
    subscription: GraphQLSubscription = await client.subscribe(request, callbacks)
    await subscription.task
```

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

### Sample Requests
#### Using `variables` and `operationName`
```py
GraphQLRequest(
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
    variables={'id': '109'},
    operationName='get_bot_name'
)
```
