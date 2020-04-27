import pytest

from aiographql.client import GraphQLError


@pytest.fixture
def error_json_extra_fields():
    return {
        "extensions": {"some_field": "foobar"},
        "message": "some error",
        "type": "NOT_FOUND",
    }


def test_handles_extra_fields_in_error(query_city, error_json_extra_fields):
    error = GraphQLError.load(error_json_extra_fields)
    assert error.__class__.__name__ == "CustomGraphQLError"
    assert isinstance(error, GraphQLError)
    assert error.message == "some error"
    assert error.extensions == {"some_field": "foobar"}
    assert error.type == "NOT_FOUND"
