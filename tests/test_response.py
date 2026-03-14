from aiographql.client.error import GraphQLError
from aiographql.client.request import GraphQLRequest
from aiographql.client.response import GraphQLResponse

def test_graphql_response_data():
    request = GraphQLRequest(query="query { city { name } }")
    json_payload = {"data": {"city": {"name": "Groningen"}}}
    response = GraphQLResponse(request=request, json=json_payload)

    assert response.data == {"city": {"name": "Groningen"}}

def test_graphql_response_data_empty():
    request = GraphQLRequest(query="query { city { name } }")
    response = GraphQLResponse(request=request, json={})

    assert response.data == {}

def test_graphql_response_errors():
    request = GraphQLRequest(query="query { city { name } }")
    json_payload = {
        "errors": [
            {"message": "City not found"},
            {"message": "Syntax error", "locations": [{"line": 1, "column": 2}]}
        ]
    }
    response = GraphQLResponse(request=request, json=json_payload)

    errors = response.errors
    assert len(errors) == 2
    assert all(isinstance(err, GraphQLError) for err in errors)
    assert errors[0].message == "City not found"
    assert errors[1].message == "Syntax error"
    assert errors[1].locations == [{"line": 1, "column": 2}]

def test_graphql_response_errors_empty():
    request = GraphQLRequest(query="query { city { name } }")
    json_payload = {"data": {"city": {"name": "Groningen"}}}
    response = GraphQLResponse(request=request, json=json_payload)

    assert response.errors == []

def test_graphql_response_query():
    query_string = "query { city { name } }"
    request = GraphQLRequest(query=query_string)
    response = GraphQLResponse(request=request, json={})

    assert response.query == query_string
