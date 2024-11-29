import pytest

from .test import AssertModelNumQueriesContext


@pytest.fixture(scope="session")
def assert_model_queries(request):
    return AssertModelNumQueriesContext(verbosity=request.config.option.verbose)
