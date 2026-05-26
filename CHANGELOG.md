# Changelog

## [1.1.0](https://github.com/abn/aiographql-client/compare/v1.0.3...v1.1.0) (2023-06-15)


### Features

* added support for Python 3.11 and 3.12
* schema caching for introspection is now enabled by default


### Miscellaneous Chores

* dropped support for Python 3.7

## [1.0.3](https://github.com/abn/aiographql-client/compare/v1.0.2...v1.0.3) (2022-09-01)


### Features

* added support for Python 3.10
* added support for GraphQL subscription sub-protocol configuration
* added documentation for custom themes (Furo, Sphinx-material)


### Bug Fixes

* fixed issue where implicit `aiohttp` client sessions were not properly closed
* updated dependencies for compatibility and security

## [1.0.2](https://github.com/abn/aiographql-client/compare/v1.0.1...v1.0.2) (2021-08-15)


### Features

* added support for Python 3.9
* switched to `src-layout` for project structure


### Bug Fixes

* resolved `aiohttp` and `connector` deprecation warnings
* ensured request headers and variables are initialized correctly (never `None`)
* updated dependencies for compatibility and security

## [1.0.1](https://github.com/abn/aiographql-client/compare/v1.0.0...v1.0.1) (2021-03-10)


### Bug Fixes

* fixed support for non-standard error fields in GraphQL responses

## [1.0.0](https://github.com/abn/aiographql-client/compare/v0.4.0...v1.0.0) (2020-11-20)


### Features

* support for GraphQL subscriptions with `on_data` and `on_error` callbacks
* added `unsubscribe_and_wait()` method for subscriptions
* support for `locations` and `path` properties in error payloads
* added client-scoped externally managed sessions
* added support for waiting during subscription initialization
* added documentation for custom session usage and async expansions


### Miscellaneous Chores

* schema caching is now at the client level
* `GraphQLRequest` objects are now frozen for consistency
* standardized `operation` property name in `GraphQLRequest`
* refactored core logic to simplify usage and improve interface
* removed the notion of transactions to streamline client behavior

## [0.4.0](https://github.com/abn/aiographql-client/compare/v0.3.0...v0.4.0) (2020-06-01)


### Features

* GitHub Actions CI/CD workflows for testing, code quality, and release
* support for world server configuration via environment variables in tests


### Miscellaneous Chores

* migrated from `graphql-core-next` (v1) to `graphql-core` (v3)
* restructured test source for better organization

## [0.3.0](https://github.com/abn/aiographql-client/compare/v0.2.0...v0.3.0) (2020-01-15)


### Features

* schema introspection and validation support
* support for dictionary items as query parameters for GET requests
* headers parameter added to the `validate` method


### Bug Fixes

* improved error handling when introspection query fails
* fix `FrozenError` in `GraphQLSchema` by setting it to `None` when necessary

## [0.2.0](https://github.com/abn/aiographql-client/compare/v0.1.0...v0.2.0) (2019-10-01)


### Features

* support for specifying additional headers at various levels: client, request, and method
* improved type hinting and documentation for the client class

## 0.1.0 (2019-07-01)


### Features

* initial release with basic GraphQL query and mutation support
* support for `aiohttp` as the default transport
