# ruff: noqa: T201
import timeit

from aiographql.client.error import GraphQLError


def benchmark_load():
    data = {
        "extensions": {"some_field": "foobar"},
        "locations": [{"line": 1, "column": 2}],
        "message": "some error",
        "path": ["a", "b"],
        "type": "NOT_FOUND",
        "extra_1": "a",
        "extra_2": "b",
        "extra_3": "c",
        "extra_4": "d",
        "extra_5": "e",
    }

    # Run the load method
    GraphQLError.load(data)


if __name__ == "__main__":
    t = timeit.Timer(benchmark_load)
    # Number of executions
    n = 100000
    new_time = t.timeit(n)
    print(f"New time for {n} executions: {new_time:.4f} seconds")
