# Changelog

## [2.0.0](https://github.com/abn/aiographql-client/compare/v1.2.0...v2.0.0) (2026-09-02)


### ⚠ BREAKING CHANGES

* 

### Features

* **client:** implement GraphQL-over-HTTP compliance ([4a0e72d](https://github.com/abn/aiographql-client/commit/4a0e72dbd72c00c2521782ab7f3f774d5a5f5f30))
* drop Python 3.10 support ([#375](https://github.com/abn/aiographql-client/issues/375)) ([a6bc8fa](https://github.com/abn/aiographql-client/commit/a6bc8fa8782100bdaa137a5fd44b59381cb12ed0))
* **subscription:** support graphql-transport-ws protocol ([8f81db7](https://github.com/abn/aiographql-client/commit/8f81db71d7b403b5c9e62fdcf935f48b784d4487))


### Performance Improvements

* optimise type hint resolution during dataclass decoding ([#360](https://github.com/abn/aiographql-client/issues/360)) ([c342d28](https://github.com/abn/aiographql-client/commit/c342d28754cd33d8195944d222f40302a3432821))


### Documentation

* auto-compute copyright year in footer ([d04cf2e](https://github.com/abn/aiographql-client/commit/d04cf2e20998caca1f2c290a2ffa6c0f93ba6378))
* document GraphQL extensions for queries and subscriptions ([#382](https://github.com/abn/aiographql-client/issues/382)) ([8afbb55](https://github.com/abn/aiographql-client/commit/8afbb5596213bd5b0272be4ae02a85f235eea289))
* document graphql-ws vs graphql-transport-ws protocol negotiation ([3c42f98](https://github.com/abn/aiographql-client/commit/3c42f9818ca308b4631571b17b24781dc1798025))

## [1.2.0](https://github.com/abn/aiographql-client/compare/v1.1.0...v1.2.0) (2026-05-27)


### Features

* add connection_init_payload for GraphQL subscriptions ([8334cff](https://github.com/abn/aiographql-client/commit/8334cffad22a26735164c124940c1753a2a8e31d)), closes [#217](https://github.com/abn/aiographql-client/issues/217)
* add GraphQL codec layer ([988f6ab](https://github.com/abn/aiographql-client/commit/988f6abcb7220b4dbdd41c53d690163402d4efe6)), closes [#236](https://github.com/abn/aiographql-client/issues/236)
* add GraphQLSession type alias for native session types ([3dc58ba](https://github.com/abn/aiographql-client/commit/3dc58ba9368ede21d37a923d951a1f079f840cf8))
* add HttpxTransport ([e994d50](https://github.com/abn/aiographql-client/commit/e994d504580219c70fb6c6adf71f9624085f7168))
* add optional pydantic support for encoding and decoding ([be20413](https://github.com/abn/aiographql-client/commit/be20413b9994f8dca7d53f85d125a8b4f7772659))
* add retry mechanism for transport errors ([31198e3](https://github.com/abn/aiographql-client/commit/31198e3e7b506eaeb16977defb00b60b6471a91a))
* add transport abstraction ([e572ae1](https://github.com/abn/aiographql-client/commit/e572ae18548a2af8609734e14a72e82a6c6ab5b0))
* allow disabling validation ([50870b7](https://github.com/abn/aiographql-client/commit/50870b7d4e4960a46fee9ceea4b22f869fed8ffd)), closes [#238](https://github.com/abn/aiographql-client/issues/238)
* auto-detect transport ([7bee013](https://github.com/abn/aiographql-client/commit/7bee01356b8476dfc6e01ae7329149fd880643c2))
* **client:** add TTL logic for expiring schemas ([578ab3f](https://github.com/abn/aiographql-client/commit/578ab3f58ce7220dc531557eedc1ac62a48a27e4))
* custom JSON serialization support ([273a8fc](https://github.com/abn/aiographql-client/commit/273a8fc9297563bf2a59cb94c8fa1dc7ac97519d)), closes [#232](https://github.com/abn/aiographql-client/issues/232)
* extend test server with authentication, add population to city model ([35b6d95](https://github.com/abn/aiographql-client/commit/35b6d955d03be64016e23c033958380306bf5fb7))
* session and client ownership model with lazy initialization ([c246e54](https://github.com/abn/aiographql-client/commit/c246e5453226614afd4635bfd3b01263166b4d2e))
* support for custom subscription transport ([ccf578b](https://github.com/abn/aiographql-client/commit/ccf578b8d7d18f492cfddf99a52376ddf8a9dcae))
* support optional transport dependencies and lazy loading ([99ef56f](https://github.com/abn/aiographql-client/commit/99ef56f391a590402e390dbb5a0fc051bfc0f5c0))
* support websockets as an alternative subscription transport ([376fb4c](https://github.com/abn/aiographql-client/commit/376fb4cc4d0980d7ab37cef3655b59813bcab12d))


### Bug Fixes

* correct Python version check in aiohttp transport ([c0348b5](https://github.com/abn/aiographql-client/commit/c0348b53749ae2b4e3aa92b8d16dd4cc44f03c15))
* correctly pass aiohttp session to subscription transport when using non-aiohttp transport ([534ba2d](https://github.com/abn/aiographql-client/commit/534ba2d4268d07c03bc84def444c53fad799f7dd))
* ensure ws_connect uses correct websocket protocol ([c969226](https://github.com/abn/aiographql-client/commit/c9692263b51136db3c088cfd37f9c79eacf1f487))
* resolve deadlock in subscriptions by increasing aiohttp connection limit ([3aef468](https://github.com/abn/aiographql-client/commit/3aef4684fb5c8d8522f15b160313ec9e33efc845))
* resolve transport-specific issues and improve environment compatibility ([c53e340](https://github.com/abn/aiographql-client/commit/c53e340b242e4b19ccf22354674e38f90ff12888))
* **tests:** import async generator for strawberry server ([f347bc0](https://github.com/abn/aiographql-client/commit/f347bc0f4b14580551df241d43fcbb3daa62c27d))
* update transport installation instructions to reference `httpx` instead of `websockets` ([0c726ad](https://github.com/abn/aiographql-client/commit/0c726adf5084ea66883f46e8253e3fed2b25f257))


### Performance Improvements

* **codec:** cache get_type_hints during decoding ([284db4c](https://github.com/abn/aiographql-client/commit/284db4c0cdc938197be2019e132a407a9b7976a2))
* **codec:** unbound type hints cache to avoid eviction thrash ([d565b87](https://github.com/abn/aiographql-client/commit/d565b875b57c0f12bbb6a33469e27eadf1f9acf9))
* **error:** optimize GraphQLError.load performance ([a6f04e1](https://github.com/abn/aiographql-client/commit/a6f04e1a3c320356cf3f2a102439f28cbbe4f1f1))


### Documentation

* add "Data Models" section, update transport abd setup instructions ([f50dd06](https://github.com/abn/aiographql-client/commit/f50dd065930719b969f67ad936d862561b488212))
* add authentication recipes ([51e22c8](https://github.com/abn/aiographql-client/commit/51e22c84f98f22bb68ae37120b40c34cc5c86284))
* add changelog and update release notes ([7d65b89](https://github.com/abn/aiographql-client/commit/7d65b89023c7b238426f86bd35fa88ec15c94a8d))
* add comprehensive local development and testing guide ([f1bb30c](https://github.com/abn/aiographql-client/commit/f1bb30c5b963ef5a6f59b8a7c861f21dc82d9afb))
* add errors and exceptions guide ([d5bf31a](https://github.com/abn/aiographql-client/commit/d5bf31a79c78d55e18d28804f3b6c42b4cdfdee7))
* add production guide ([35b2756](https://github.com/abn/aiographql-client/commit/35b2756aab057bda55fcce3e4f78820fb707b50e))
* add scenario-based example scripts for common use cases ([b7b46a6](https://github.com/abn/aiographql-client/commit/b7b46a65c8d1392d4aa77c993893f85224525aed))
* clarify transport options and installation instructions ([abe567b](https://github.com/abn/aiographql-client/commit/abe567b9d0a36d46140b080e221ae164fbcec8f9))
* correct WebsocketSubscriptionTransport name ([5963faf](https://github.com/abn/aiographql-client/commit/5963fafa74af0c4e4536656a425de492de480cef))
* fix usage example in transport documentation ([01f671c](https://github.com/abn/aiographql-client/commit/01f671c3e4cdd561999b4345460f3d72cd132d4c))
* improve documentation and update examples ([1b85f02](https://github.com/abn/aiographql-client/commit/1b85f024bf9d39fda5006c3259e9bcfa94c15b55))
* rebuild documentation site with Shibuya theme and modern Sphinx stack ([7870abf](https://github.com/abn/aiographql-client/commit/7870abfb27d875cd709cd3c7b152093356e39ec1))
* refresh contributing guide and document release process ([398ec33](https://github.com/abn/aiographql-client/commit/398ec330b76cff79591c27e556074d5ce0817dfb))
* remove duplicate retry mechanism entry from changelog ([434295c](https://github.com/abn/aiographql-client/commit/434295c0ec37f1bef7cdef834a317a2064731abc))
* suppress SyntaxWarning from css_html_js_minify and update docs build environment ([c48a229](https://github.com/abn/aiographql-client/commit/c48a229beb89f7ff0abe79c0fa1cb399aac4cd7e))
* update Sphinx theme options with custom labels for TOC and search ([f911e77](https://github.com/abn/aiographql-client/commit/f911e77c79d31dc398e95db85b614b8f67357a99))
* use release-please generated CHANGELOG.md in Sphinx docs ([ee80ea8](https://github.com/abn/aiographql-client/commit/ee80ea8bf1a8459178e32182e21f00315eab25b9))

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
