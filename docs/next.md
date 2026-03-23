# Next

## Added
- New transport abstraction layer with support for multiple protocols:
  - `AiohttpTransport` (default, requires `aiohttp`)
  - `HttpxTransport` (requires `httpx`)
  - `WebsocketTransport` (requires `websockets`)
- Auto-detection of transport based on installed dependencies and environment.
- GraphQL codec layer with support for custom encoding and decoding:
  - `DefaultGraphQLCodec` for standard JSON support.
  - `PydanticGraphQLCodec` for Pydantic v2 model support.
  - Support for `dataclasses` out of the box.
- Lazy initialization of client sessions with ownership management.
- Retry mechanism for transport errors (e.g., connection issues).
- Support for `connection_init_payload` in GraphQL subscriptions.
- Support for Python 3.13 and 3.14.
- Added "Data Models" and scenario-based examples to documentation.

## Changed
- Migrated project to PEP 621 with static dependencies in `pyproject.toml`.
- Switched to `ruff` for linting and formatting.
- Modernized CI/CD pipeline to use Podman and tox.
- Improved subscription handling to prevent deadlocks with `aiohttp` connection limits.
- Improved type hints and type checks across the codebase.

## Fixed
- Fixed websocket protocol selection in `ws_connect`.
- Improved error handling for `aiohttp` and `httpx` transports.
- Fixed several mypy and linting issues.
