:layout: landing

.. raw:: html

   <div class="docs-hero">
     <img class="docs-hero-logo only-light"
          src="_static/aiographql-client-logo.svg"
          alt="aiographql-client" />
     <img class="docs-hero-logo only-dark"
          src="_static/aiographql-client-logo-white.svg"
          alt="aiographql-client" />
     <h1>Async GraphQL Client</h1>
     <p class="docs-hero-tagline">
       An asynchronous GraphQL client for Python and asyncio &mdash; built on
       <code>aiohttp</code> / <code>httpx</code> and <code>graphql-core</code>.
     </p>
     <div class="docs-hero-badges">
       <a href="https://pypi.org/project/aiographql-client/"><img
           alt="PyPI"
           src="https://img.shields.io/pypi/v/aiographql-client?color=ec407a&amp;label=pypi&amp;logo=pypi&amp;logoColor=white" /></a>
       <a href="https://pypi.org/project/aiographql-client/"><img
           alt="Python versions"
           src="https://img.shields.io/pypi/pyversions/aiographql-client?color=ec407a&amp;logo=python&amp;logoColor=white" /></a>
       <a href="https://aiographql-client.readthedocs.io/en/latest/"><img
           alt="Read the Docs"
           src="https://img.shields.io/readthedocs/aiographql-client?color=ec407a&amp;label=docs&amp;logo=readthedocs&amp;logoColor=white" /></a>
       <a href="https://github.com/abn/aiographql-client/blob/main/LICENSE"><img
           alt="License"
           src="https://img.shields.io/pypi/l/aiographql-client?color=ec407a" /></a>
     </div>
   </div>

.. tab-set::

   .. tab-item:: pip

      .. code-block:: shell

         pip install "aiographql-client[aiohttp,pydantic]"

   .. tab-item:: poetry

      .. code-block:: shell

         poetry add "aiographql-client[aiohttp,pydantic]"

.. grid:: 1 1 3 3
    :gutter: 3
    :margin: 4 4 0 0

    .. grid-item::

        .. button-ref:: introduction
            :ref-type: ref
            :color: primary
            :expand:

            Get started

    .. grid-item::

        .. button-ref:: api
            :ref-type: ref
            :color: secondary
            :outline:
            :expand:

            API reference

    .. grid-item::

        .. button-link:: https://github.com/abn/aiographql-client
            :color: secondary
            :outline:
            :expand:

            GitHub

.. raw:: html

   <h2 class="docs-section-heading">Why aiographql-client</h2>

.. grid:: 1 2 2 3
    :gutter: 3

    .. grid-item-card:: :octicon:`zap` Async-first

        Built from the ground up on ``asyncio``. No sync shim, no thread pool.

    .. grid-item-card:: :octicon:`plug` Multiple transports

        ``aiohttp`` (default) and ``httpx``. Swap freely, share sessions for
        production-grade connection pooling.

    .. grid-item-card:: :octicon:`broadcast` Subscriptions

        First-class GraphQL subscriptions over WebSockets via
        ``aiohttp`` or ``websockets``.

    .. grid-item-card:: :octicon:`shield-check` Schema validation

        Client-side query validation powered by ``graphql-core``.

    .. grid-item-card:: :octicon:`package` Bring your own models

        Decode straight into ``dataclasses`` or ``Pydantic`` models with
        explicit codecs.

    .. grid-item-card:: :octicon:`rocket` Production-ready

        Battle-tested in high-throughput async services.

.. raw:: html

   <h2 class="docs-section-heading">Explore</h2>

.. grid:: 1 2 2 3
    :gutter: 3

    .. grid-item-card:: Introduction
        :link: introduction
        :link-type: ref

        Install, quick start, and the mental model.

    .. grid-item-card:: Examples
        :link: examples
        :link-type: ref

        Queries, mutations, subscriptions, validation, data models.

    .. grid-item-card:: Transports
        :link: transport
        :link-type: ref

        aiohttp vs httpx, sessions, timeouts, retries, SOCKS proxies.

    .. grid-item-card:: Data models
        :link: data-models
        :link-type: doc

        Dataclasses and Pydantic decoding patterns.

    .. grid-item-card:: Python API
        :link: api
        :link-type: ref

        Full reference for client, transport, data, constants, exceptions.

    .. grid-item-card:: Contributing
        :link: contributing
        :link-type: doc

        Local setup, tests, conventions, release process.

.. toctree::
   :hidden:
   :caption: Introduction

   introduction

.. toctree::
   :hidden:
   :caption: Reference

   examples
   transport
   data-models
   errors
   api
   changelog

.. toctree::
   :hidden:
   :caption: Community

   contributing
