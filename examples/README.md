# Examples

This directory contains several scenario-based scripts that demonstrate the capabilities of the `aiographql-client`. All examples use a local Strawberry GraphQL server for demonstration.

## Setup: Start the Strawberry Server

To run any of the example scripts, you must first start the Strawberry server. This project includes a pre-configured server in `docker-compose.yaml`.

```bash
# From the project root, build and run the strawberry-server
podman compose run --build strawberry-server
```

The server will be accessible at `http://localhost:5000/graphql`.

## Running the Examples

Ensure you have installed the project dependencies:

```bash
poetry install --extras pydantic
```

Then, you can run any of the following scripts from the project root:

| Script | Description |
| :--- | :--- |
| `basic_queries.py` | Simple query operations, including arguments and nested fields. |
| `data_models.py` | Using Pydantic models for type-safe data handling. |
| `dataclass_models.py` | Using standard Python `dataclasses` with `query_data_as`. |
| `authenticated_requests.py` | Using headers to perform authenticated requests. |
| `mutations.py` | Performing mutations using variables. |
| `subscriptions.py` | Real-time updates using subscriptions and callbacks. |
| `httpx_transport.py` | Using the `httpx` transport and shared sessions. |
| `custom_serialization.py` | Custom `GraphQLSerializer` and `GraphQLCodec` implementations. |

### Example command to run a script:

```bash
poetry run python examples/basic_queries.py
```

## Scenario Descriptions

### [Basic Queries](basic_queries.py)
Demonstrates the most common use case: sending a string query to the server and accessing the result. It covers simple fields, fields with arguments, and nested data structures.

### [Data Models](data_models.py)
Shows how to leverage Pydantic models with `query_data_as`. This approach provides full type safety, IDE autocompletion, and automatic validation of the server's response.

### [Dataclass Models](dataclass_models.py)
Demonstrates how to use standard Python `dataclasses` with `query_data_as`. This provides a lightweight alternative to Pydantic for structured data handling.

### [Authenticated Requests](authenticated_requests.py)
Explains how to set global headers at the client level or override them for individual requests. This is essential for working with APIs that require bearer tokens or API keys.

### [Mutations](mutations.py)
Focuses on updating data. It highlights the importance of using GraphQL variables within a `GraphQLRequest` object to create clean and secure mutations.

### [Subscriptions](subscriptions.py)
Demonstrates real-time communication. It shows how to use callbacks (`on_data`, `on_error`) to handle streams of data from the server, such as live notifications or progress counters.

### [Httpx Transport](httpx_transport.py)
Shows how to use `HttpxTransport`, allowing you to provide a custom or shared `httpx.AsyncClient`. This is useful for sharing sessions or using `httpx`-specific features.

### [Custom Serialization](custom_serialization.py)
Explains how to implement a custom `GraphQLSerializer` for JSON handling and a custom `GraphQLCodec` for encoding and decoding complex Python types (like `datetime`) in variables and responses.
