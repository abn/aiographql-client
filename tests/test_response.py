import pytest

from aiographql.client import GraphQLRequest, GraphQLResponse, GraphQLError


@pytest.fixture
def json_error_response():
    return {
        "errors": [
            {
                "extensions": {"some_field": "foobar"},
                "message": "some error",
                "type": "NOT_FOUND",
            },
        ]
    }


def test_handles_extra_fields_in_error(query_city, json_error_response):
    response = GraphQLResponse(request=GraphQLRequest(query_city), json=json_error_response)
    assert response.errors == [
        GraphQLError(
            extensions={"some_field": "foobar", "_unknown_fields":{"type": "NOT_FOUND"}}, message="some error"
        )
    ]
