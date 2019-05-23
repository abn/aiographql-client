def pytest_addoption(parser):
    parser.addoption(
        "--pokemon-server",
        action="store",
        default="http://localhost:5000",
        help="GraphQL server to use for integration tests",
    )
