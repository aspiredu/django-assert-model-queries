import pytest

from .test import AssertModelQueries


@pytest.fixture(scope="session")
def assert_model_queries():
    """
    An assertion fixture that is used as a context manager.

    Usage:

        def test_something(self, assert_model_queries):
            with assert_model_queries({"MyModel": 1}):
                do_something()

    """
    return AssertModelQueries()
