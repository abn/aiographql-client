.. _contributing:

Contributing
============

Reporting Issues
----------------

If you are using this package and are encountering issues, please feel free to raise them
at on our `issue tracker`_.

.. _issue tracker: https://github.com/abn/aiographql-client/issues

Providing Feedback
------------------

This client was developed with a limited set of use cases in mind. And therein, can be biased
in various places. Any feedback regarding what could be improved, added or changes can also be
submitted similar to reporting issues, on our `issue tracker`_.

Code Contributions
------------------

Code contributions in the form of bugfixes, improvements or new features are always welcome.
All that we ask, is that you do make sure the rationale for the change is described if it is
more than a simple change. The current open change requests can be seen are available `here`_.

.. _here: https://github.com/abn/aiographql-client/pulls

Documentation
-------------

Improvements and additions to our documentation are always welcome. From typo fixes, to
documenting undocumented features, or structural changes. Everything is welcome.

Local Development
-----------------

Setting Up
~~~~~~~~~~

To set up your local development environment, you will need `Poetry`_ (>= 2.0).

.. code-block:: shell

    # Install dependencies including all optional extras and dev/test/docs groups
    poetry install --all-extras --with dev,test,docs

    # Install pre-commit hooks (runs ruff, formatting, and conventional commit checks)
    poetry run pre-commit install --hook-type pre-commit --hook-type commit-msg

Running Tests
~~~~~~~~~~~~~

The project uses ``pytest`` for testing and ``tox`` to manage the test matrix across
Python versions and HTTP transports (``aiohttp``, ``httpx``, or both).

Integration tests require running GraphQL servers (Hasura, Apollo v2, Strawberry), which
are managed via ``podman compose`` (or ``docker-compose``).

.. code-block:: shell

    # Start test servers
    podman compose up -d

    # Run the full suite directly with pytest
    poetry run pytest

    # Or run via tox for a specific Python version and transport combination
    poetry run tox -e py312-aiohttp
    poetry run tox -e py312-httpx
    poetry run tox -e py312-all

The pytest configuration waits up to 300 seconds for the Hasura server to become ready
before running tests, so you do not need to manually verify server readiness after
``podman compose up``. Tests that depend on Apollo v2 or Strawberry are skipped if the
corresponding server is unavailable.

Coverage data is written to ``.coverage/`` and merged across tox environments. To
generate an HTML report:

.. code-block:: shell

    poetry run tox -e report

Environment Variables
^^^^^^^^^^^^^^^^^^^^^

If you need to customize the GraphQL server endpoints for testing, set the following
environment variables (or pass equivalent ``--server-*`` options to pytest):

- ``GRAPHQL_ENDPOINT_WORLD_SERVER``: Hasura world database endpoint (default: ``http://127.0.0.1:8080/v1/graphql``)
- ``GRAPHQL_ENDPOINT_APOLLO_V2``: Apollo Server v2 endpoint (default: ``http://127.0.0.1:4000/graphql``)
- ``GRAPHQL_ENDPOINT_STRAWBERRY``: Strawberry server endpoint (default: ``http://127.0.0.1:5000/graphql``)

Cross-Platform Testing
^^^^^^^^^^^^^^^^^^^^^^

The CI test matrix exercises Python 3.11 through 3.14 across the ``aiohttp``, ``httpx``,
and combined transport configurations on Ubuntu. Contributors typically run tests on
their preferred platform locally; the automated CI ensures the codebase remains
compatible across the supported Python versions.

Code Quality
~~~~~~~~~~~~

Linting and formatting are handled by `Ruff`_, and type checking by `mypy`_. Both are
configured in ``pyproject.toml`` and run automatically via the pre-commit hooks when
installed.

.. code-block:: shell

    # Lint and auto-fix
    poetry run ruff check .

    # Format
    poetry run ruff format .

    # Type-check
    poetry run mypy

    # Run all pre-commit hooks against the full tree
    poetry run pre-commit run --all-files

Building Documentation
~~~~~~~~~~~~~~~~~~~~~~

You can build the documentation locally using ``tox``:

.. code-block:: shell

    poetry run tox -e docs

The generated documentation will be available in ``docs/_build/html/index.html``.

Commit Messages
---------------

This project follows the `Conventional Commits`_ specification. Commit messages are
validated locally by a pre-commit hook (``conventional-pre-commit``), and pull request
titles are validated in CI by the ``PR Title Check`` workflow.

A typical commit message looks like:

.. code-block:: text

    feat(transport): add httpx subscription support

    Optional longer description explaining the change.

The commit type drives the automated release process (see below):

- ``feat``: a new feature → minor version bump
- ``fix``: a bug fix → patch version bump
- ``feat!`` / ``BREAKING CHANGE:`` footer → major version bump
- ``chore``, ``docs``, ``refactor``, ``test``, ``ci``, ``build``, ``style``, ``perf``: no version bump

When opening a pull request, ensure the **PR title** itself is a valid Conventional
Commit message. The PR title is what release-please consumes when the commits are
squash-merged.

Release Process
---------------

Releases are fully automated via `release-please`_ and the ``Publish Release`` GitHub
Actions workflow (``.github/workflows/release.yml``). Maintainers do not need to
manually edit ``pyproject.toml``, tag commits, or push to PyPI.

End-to-end flow
~~~~~~~~~~~~~~~

1. Conventional commits land on ``main`` via pull requests.
2. On every push to ``main``, the ``release-please`` action inspects the commits made
   since the last release and opens (or updates) a release pull request titled
   ``chore(main): release <next-version>``. This PR contains:

   - The version bump in ``pyproject.toml`` (under ``[project] version``).
   - The regenerated ``CHANGELOG.md`` entry, grouped by Conventional Commit type.

3. While additional commits continue to land on ``main``, ``release-please``
   continuously updates the same release PR — recomputing the proposed version and
   appending new changelog entries — until it is merged or closed.
4. When a maintainer merges the release PR, ``release-please`` creates a GitHub
   Release and a corresponding ``vX.Y.Z`` git tag pointing at the merge commit.
5. The release creation triggers the ``publish`` job in the same workflow, which
   builds the distribution with ``poetry build`` and publishes it to PyPI using the
   `PyPI Trusted Publishers`_ mechanism (OIDC; no long-lived API token is stored in
   the repository).

The Sphinx documentation hosted on `Read the Docs`_ is built automatically from the
``main`` branch and from tagged releases.

How version bumps are computed
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``release-please`` is configured with ``release-type: python``, which follows
`Semantic Versioning`_ and derives the next version from the Conventional Commit
types present since the previous tag:

.. list-table::
   :header-rows: 1
   :widths: 30 20 50

   * - Commit type
     - Bump (≥ 1.0.0)
     - Notes
   * - ``feat: …``
     - **minor** (``1.2.0 → 1.3.0``)
     - New, backwards-compatible functionality.
   * - ``fix: …``
     - **patch** (``1.2.0 → 1.2.1``)
     - Backwards-compatible bug fix.
   * - ``feat!: …`` / ``fix!: …`` / footer ``BREAKING CHANGE:``
     - **major** (``1.2.0 → 2.0.0``)
     - Any backwards-incompatible change. The ``!`` after the type, or a
       ``BREAKING CHANGE:`` footer in the commit body, is what marks it as breaking.
   * - ``chore``, ``docs``, ``refactor``, ``test``, ``ci``, ``build``, ``style``, ``perf``, ``revert``
     - none
     - Recorded under "Miscellaneous Chores" / similar sections in the changelog,
       but do not trigger a release by themselves.

The highest applicable bump wins: a release containing one ``feat`` and one ``fix``
results in a single minor bump.

If the only commits since the last tag are bump-less types (``chore``, ``docs``,
etc.), ``release-please`` will not open a release PR at all. To force a release in
that situation, push a commit using the ``release-as`` footer convention, for
example as an empty commit on ``main``:

.. code-block:: shell

    git commit --allow-empty -m "chore: release 1.2.1" \
        -m "Release-As: 1.2.1"

Pre-1.0 behavior
^^^^^^^^^^^^^^^^

While the project version is still ``0.x.y``, ``release-please`` uses a conservative
mapping in accordance with SemVer's pre-1.0 conventions: breaking changes bump the
**minor** component, and ``feat`` commits bump the **patch** component. Once the
project ships ``1.0.0``, the table above applies.

Pre-releases
^^^^^^^^^^^^

The version declared in ``pyproject.toml`` may carry a pre-release suffix (for
example ``1.2.0a0``) between releases. ``release-please`` will strip the pre-release
suffix when computing the next stable release version. Ad-hoc pre-releases (alpha,
beta, rc) are not part of the normal automated flow; if one is needed, cut it
manually by tagging from ``main`` and running ``poetry publish`` against PyPI from a
trusted environment.

What contributors need to do
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Write Conventional Commit messages — or, more importantly, ensure the **PR title**
  is a valid Conventional Commit, since merges to ``main`` are squashed and the PR
  title becomes the commit message that ``release-please`` reads.
- Mark backwards-incompatible changes with ``feat!`` / ``fix!`` or a
  ``BREAKING CHANGE:`` footer.
- Do **not** hand-edit ``pyproject.toml`` ``version``, ``CHANGELOG.md``, or create
  git tags — ``release-please`` owns all of these artifacts.

.. _Poetry: https://python-poetry.org
.. _Ruff: https://docs.astral.sh/ruff/
.. _mypy: https://mypy.readthedocs.io/
.. _Conventional Commits: https://www.conventionalcommits.org/
.. _release-please: https://github.com/googleapis/release-please
.. _Semantic Versioning: https://semver.org/
.. _PyPI Trusted Publishers: https://docs.pypi.org/trusted-publishers/
.. _Read the Docs: https://aiographql-client.readthedocs.io/
