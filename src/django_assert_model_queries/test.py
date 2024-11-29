from __future__ import annotations
import difflib
import pprint
from unittest.util import _common_shorten_repr

from django.db import DEFAULT_DB_ALIAS, connections
from django.db.models import Model
from django.test.utils import CaptureQueriesContext

from .patch import patch_sql_compilers_for_debugging, reset_query_counter, query_counts


try:
    import pytest
except ImportError:  # pragma: no cover
    pytest = None


def normalize_key(key: str | Model | type[Model]) -> str:
    if isinstance(key, str):
        return key
    if isinstance(key, Model):
        return key._meta.label
    if isinstance(key, type) and issubclass(key, Model):
        return key._meta.label
    raise TypeError(f"Expected str, Model, or Type[Model], got {type(key)}")


def parse_counts(raw: list | dict | tuple | None) -> dict:
    if raw is None:
        return {}
    if isinstance(raw, dict):
        raw = raw.items()
    return {normalize_key(key): count for key, count in raw}


class ExpectedModelCountsNotSet(ValueError):
    """
    The expected model counts can be passed as a constructor
    argument or as a context manager argument.
    """


class AssertModelQueries(CaptureQueriesContext):
    unpatch = None

    def __init__(
        self,
        expected_model_counts=None,
        strict=True,
        ignore=None,
        test_case=None,
        connection=None,
    ):
        """
        Assert the number of queries per model match what's expected.


        Usage:

            with AssertModelQueries({"MyModel": 1}):
                do_something()


        :param expected_model_counts: The pairs of models to counts. The
                                      keys can be model classes, instances
                                      or the model label such as
                                      `app_name.ModelName`. This can be a
                                      list or tuple or tuples, or a dictionary.
        :param strict: Defaults to True. When True, any difference in counts
                       for any model causes a failure. When False, only
                       differences in model counts for those specified in
                       `expected_model_counts` are evaluated. Warning, this
                       can hide N+1 issues.
        :param ignore: A collection of model classes, instances or strings of
                       the model label's such as `app_name.ModelName`. Any
                       queries due to these models are not evaluated. This is
                       helpful when wanting to ignore queries that happen on
                       every request such as when using a database backed
                       session.
        :param test_case: The test case to evaluate. This is only used
                          by the Django TestCase helper class.
        :param connection: The database connection to use. If not
                           specified, it uses the default.
        """
        self.strict = strict
        self.ignore_models = (
            {normalize_key(instance) for instance in ignore} if ignore else set()
        )
        self.test_case = test_case
        self.expected_model_counts = (
            parse_counts(expected_model_counts)
            if expected_model_counts is not None
            else None
        )
        connection = connection or connections[DEFAULT_DB_ALIAS]
        super().__init__(connection)

    def find_actual(self, actual, expected):
        """
        Identify relevant models that had queries based on
        strictness and any ignored models.
        """
        if not self.strict:
            actual = {
                model: count for model, count in actual.items() if model in expected
            }
        if self.ignore_models:
            actual = {
                model: count
                for model, count in actual.items()
                if model not in self.ignore_models
            }
        return actual

    def __enter__(self):
        """Patch the compiler classes to collect queries per model"""
        reset_query_counter()
        if self.expected_model_counts is None:
            raise ExpectedModelCountsNotSet(
                "The expected model counts can be passed as a constructor argument or as a context manager argument."
            )
        self.unpatch = patch_sql_compilers_for_debugging()
        return super().__enter__()

    def __exit__(self, exc_type, exc_value, traceback):
        """
        When exiting from a context manager's scope, evaluate
        the number of queries per model against expectations.

        This also unpatches the compiler classes and resets the
        query counter.
        """
        super().__exit__(exc_type, exc_value, traceback)

        expected = self.expected_model_counts
        actual = dict(self.find_actual(query_counts.get().copy(), expected))

        self.unpatch()
        reset_query_counter()

        if exc_type is not None:
            return

        self.handle_assertion(actual, expected)
        self.expected_model_counts = None

    def __call__(self, expected_model_counts=None):
        """
        Support reconfiguring the expected model counts
        when creating a new context manager.
        """
        if expected_model_counts is not None:
            self.expected_model_counts = parse_counts(expected_model_counts)
        return self

    def handle_assertion(self, actual, expected):
        """
        Evaluate the differences and render a failure
        message if needed.
        """
        if self.test_case:
            self.test_case.assertDictEqual(
                actual,
                expected,
                self.failure_message(actual, expected),
            )
        elif pytest:
            if actual != expected:
                pytest.fail(self.failure_message(actual, expected))
        else:
            assert actual == expected, self.failure_message(actual, expected)

    def failure_message(self, actual, expected):
        """
        Generate a failure message.

        This is based on Django's _AssertNumQueriesContext'
        failure message.
        """
        short = "%s != %s" % _common_shorten_repr(actual, expected)
        diff = "\n" + "\n".join(
            difflib.ndiff(
                pprint.pformat(actual).splitlines(),
                pprint.pformat(expected).splitlines(),
            )
        )
        queries = "\n\nAll queries:\n" + "\n".join(
            q["sql"] for q in self.captured_queries
        )
        return short + diff + queries


class ModelNumQueriesHelper:
    """
    Inherit from this mixin to use `self.assertModelQueries`.
    """

    def assertModelQueries(
        self, expected_model_counts, using=DEFAULT_DB_ALIAS, **kwargs
    ):
        """
        A helper assertion method that is used as a context manager.

        Usage:

            def test_something(self):
                with self.assertModelQueries({"MyModel": 1}):
                    do_something()

        """
        conn = connections[using]

        return AssertModelQueries(
            expected_model_counts=expected_model_counts, test_case=self, connection=conn
        )
