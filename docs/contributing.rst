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

To set up your local development environment, you will need `Poetry`_.

.. code-block:: shell

    # Install dependencies
    poetry install --all-extras

Running Tests
~~~~~~~~~~~~~

The project uses `pytest` for testing. Some tests require running GraphQL servers (Hasura, Apollo v2), which can be managed using `podman compose` or `docker-compose`.

.. code-block:: shell

    # Start test servers
    podman compose up -d

    # Run tests
    poetry run pytest

Building Documentation
~~~~~~~~~~~~~~~~~~~~~~

You can build the documentation locally using `tox` or `make`.

Using tox:

.. code-block:: shell

    tox -e docs

The generated documentation will be available in ``docs/_build/html/index.html``.

.. _Poetry: https://python-poetry.org
