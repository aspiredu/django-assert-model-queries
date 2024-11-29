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


class AssertModelNumQueriesContext(CaptureQueriesContext):
    unpatch = None

    def __init__(
        self,
        expected_model_counts=None,
        strict=True,
        ignore=None,
        test_case=None,
        connection=None,
        verbosity=0,
    ):
        self.strict = strict
        self.ignore_models = (
            {normalize_key(instance) for instance in ignore} if ignore else set()
        )
        self.verbosity = verbosity
        self.test_case = test_case
        self.expected_model_counts = (
            parse_counts(expected_model_counts)
            if expected_model_counts is not None
            else None
        )
        connection = connection or connections[DEFAULT_DB_ALIAS]
        super().__init__(connection)

    def find_actual(self, actual, expected):
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
        reset_query_counter()
        if self.expected_model_counts is None:
            raise ExpectedModelCountsNotSet(
                "The expected model counts can be passed as a constructor argument or as a context manager argument."
            )
        self.unpatch = patch_sql_compilers_for_debugging()
        return super().__enter__()

    def __exit__(self, exc_type, exc_value, traceback):
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
        if expected_model_counts is not None:
            self.expected_model_counts = parse_counts(expected_model_counts)
        return self

    def handle_assertion(self, actual, expected):
        if self.test_case:
            self.test_case.assertDictEqual(
                actual,
                expected,
                self.failure_message(actual, expected),
            )
        elif pytest and actual != expected:
            pytest.fail(self.failure_message(actual, expected))

    def failure_message(self, actual, expected):
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
    def assertModelNumQueries(
        self, expected_model_counts, using=DEFAULT_DB_ALIAS, **kwargs
    ):
        conn = connections[using]

        return AssertModelNumQueriesContext(
            expected_model_counts=expected_model_counts, test_case=self, connection=conn
        )
