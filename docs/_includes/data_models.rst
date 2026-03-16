.. _data_models:

Bring Your Own Models
=====================

The ``aiographql-client`` library allows you to use your own Python models, such as ``dataclasses`` or ``Pydantic`` models, for both input variables and output decoding. This "bring your own models" workflow is **explicit**—the client does not automatically decode responses into models unless you request it.

Raw usage and typed usage are kept separate, giving you full control over when and how you use your models.

Supported Model Types
---------------------

The client includes a default codec that supports:

* **Standard Python Dataclasses**: Both for input and output.
* **Pydantic Models**: Support for Pydantic v2 (Pydantic >= 2.0 is required).
* **Externally Generated Models**: Any models generated from tools like ``datamodel-code-generator`` (which typically generates Pydantic models) work seamlessly.

Dataclasses
-----------

You can pass a dataclass instance directly as a GraphQL variable. When receiving data, you can use ``query_data_as`` to decode the result into a dataclass.

.. code-block:: python

    from dataclasses import dataclass
    from aiographql.client import GraphQLClient

    @dataclass
    class CreateUserInput:
        name: str

    @dataclass
    class User:
        id: int
        name: str

    client = GraphQLClient(endpoint="http://localhost/graphql")

    # Input: Passing a dataclass in variables
    user_input = CreateUserInput(name="Alice")
    query = "mutation CreateUser($input: CreateUserInput) { createUser(input: $input) { id name } }"

    # Output: Explicitly decoding into a dataclass
    # The 'path' argument specifies where in the response JSON to find the data
    user = await client.query_data_as(
        query,
        User,
        variables={"input": user_input},
        path="createUser"
    )

    print(user.id, user.name)
    # 1 Alice

Pydantic Models
---------------

Pydantic models are supported for both input and output. The client will automatically detect if Pydantic is installed and use its validation and serialization features.

.. code-block:: python

    from pydantic import BaseModel
    from aiographql.client import GraphQLClient

    class User(BaseModel):
        id: int
        name: str

    client = GraphQLClient(endpoint="http://localhost/graphql")

    query = "{ user(id: 1) { id name } }"

    # Explicitly decoding into a Pydantic model
    user = await client.query_data_as(query, User, path="user")

    print(user.id, user.name)
    # 1 Alice

Externally Generated Models
---------------------------

If you use tools like `datamodel-code-generator <https://koxudaxi.github.io/datamodel-code-generator/>`_ to generate Python models from a GraphQL schema or JSON response, you can use those generated models directly with the client's ``query_data_as`` method.

Because these tools typically generate Pydantic models or dataclasses, they are fully compatible with the client's built-in codec.

.. note::
   The ``aiographql-client`` does not include built-in schema code generation. You should use external tools to generate your models and then use them with the client.

Explicit vs Automatic Decoding
------------------------------

It is important to note that decoding is **explicit**.

* ``client.query(...)`` returns a ``GraphQLResponse`` object where ``response.data`` is a raw dictionary.
* ``client.query_data_as(..., model_class, path="...")`` performs the query and then explicitly decodes the data at the specified path into the provided ``model_class``.

This separation ensures that you can always access the raw response if needed.
