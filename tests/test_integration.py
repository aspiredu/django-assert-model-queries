from textwrap import dedent
from unittest.mock import Mock

import pytest
from django.db.models import Count

from django_assert_model_queries import AssertModelQueriesContext
from django_assert_model_queries.patch import (
    query_counts,
    reset_query_counter,
    patch_sql_compilers_for_debugging,
)

from django_assert_model_queries.test import (
    normalize_key,
    parse_counts,
    ExpectedModelCountsNotSet,
)
from tests.testapp.models import Community


class TestPatching:
    @pytest.fixture
    def patch(self):
        unpatch = patch_sql_compilers_for_debugging()
        reset_query_counter()
        yield
        unpatch()
        reset_query_counter()

    @pytest.mark.parametrize("using_db", ["default", "mysql"], ids=["sqlite", "mysql"])
    @pytest.mark.django_db(databases=["default", "mysql"])
    def test_unpatched_compilers(self, using_db):
        manager = Community.objects.using(using_db)
        manager.create(name="test")
        manager.update(name="new")
        manager.get(name="new")
        # Use a limit to hit the SQLAggregateCompiler
        manager.all()[:1].aggregate(count=Count("topics__id"))
        manager.prefetch_related("topics", "chapters").get(name="new")
        manager.all().delete()
        assert query_counts.get() == {}

    @pytest.mark.parametrize("using_db", ["default", "mysql"], ids=["sqlite", "mysql"])
    @pytest.mark.django_db(databases=["default", "mysql"])
    def test_patched_compilers(self, using_db, patch):
        manager = Community.objects.using(using_db)
        manager.create(name="test")
        manager.update(name="new")
        manager.get(name="new")
        # Use a limit to hit the SQLAggregateCompiler
        manager.all()[:1].aggregate(count=Count("topics__id"))
        assert query_counts.get() == {"testapp.Community": 4}
        manager.prefetch_related("topics", "chapters").get(name="new")
        assert query_counts.get() == {
            "testapp.Community": 5,
            "testapp.Chapter": 1,
            "testapp.Topic": 1,
        }
        manager.all().delete()
        assert query_counts.get() == {
            "testapp.Community": 7,
            "testapp.Chapter": 2,
            "testapp.Topic": 1,
            "testapp.Community_topics": 1,
        }


class TestAssertModelQueriesContext:
    @pytest.fixture
    def assert_context(self):
        context = AssertModelQueriesContext(
            connection=Mock(queries=[{"sql": "SELECT * FROM testapp.community"}])
        )
        context.initial_queries = 0
        context.final_queries = 1
        return context

    @pytest.mark.django_db
    def test_call_expects_overrides_init(self):
        context = AssertModelQueriesContext({"testapp.Community": 0})
        with context({"testapp.Community": 1}):
            assert Community.objects.first() is None
            assert context.expected_model_counts == {"testapp.Community": 1}

    def test_failure_message(self, assert_context):
        assert assert_context.failure_message(
            {"djangonaut.Space": 1}, {"django.Commons": 2}
        ) == dedent(
            """            {'djangonaut.Space': 1} != {'django.Commons': 2}
            - {'djangonaut.Space': 1}
            + {'django.Commons': 2}

            All queries:
            SELECT * FROM testapp.community"""
        )
        assert assert_context.failure_message({"djangonaut.Space": 1}, {}) == dedent(
            """            {'djangonaut.Space': 1} != {}
            - {'djangonaut.Space': 1}
            + {}

            All queries:
            SELECT * FROM testapp.community"""
        )
        assert assert_context.failure_message({}, {"django.Commons": 2}) == dedent(
            """            {} != {'django.Commons': 2}
            - {}
            + {'django.Commons': 2}

            All queries:
            SELECT * FROM testapp.community"""
        )

    def test_expected_model_counts_not_set(self):
        context = AssertModelQueriesContext()
        with pytest.raises(ExpectedModelCountsNotSet):
            with context():
                pass  # pragma: no cover

    def test_find_actual(self, assert_context):
        assert assert_context.find_actual({"a": 1}, {"b": 2}) == {"a": 1}

    def test_find_actual_not_strict(self, assert_context):
        assert_context.strict = False
        assert assert_context.find_actual({"a": 1}, {"b": 2}) == {}
        assert assert_context.find_actual({"a": 1, "c": 3}, {"b": 2, "c": 3}) == {
            "c": 3
        }

    def test_find_actual_ignore_models(self, assert_context):
        assert_context.ignore_models = {"b", "c"}
        assert assert_context.find_actual({"a": 1}, {"b": 2}) == {"a": 1}
        assert assert_context.find_actual({"a": 1, "b": 2, "c": 3}, {}) == {"a": 1}

    @pytest.mark.django_db
    def test_exception_still_unpatches(self):
        context = AssertModelQueriesContext()

        class KnownException(Exception):
            pass

        with pytest.raises(KnownException):
            with context({"testapp.Community": 1}):
                assert Community.objects.first() is None
                assert query_counts.get() == {"testapp.Community": 1}
                raise KnownException()
        assert query_counts.get() == {}


class TestUtils:
    @pytest.mark.parametrize(
        "key, expected",
        [
            ("key", "key"),
            (Community, "testapp.Community"),
            (Community(), "testapp.Community"),
        ],
    )
    def test_normalize_key(self, key, expected):
        assert normalize_key(key) == expected

    def test_normalize_key_error(self):
        with pytest.raises(TypeError):
            normalize_key(None)

    @pytest.mark.parametrize(
        "input, expected",
        [
            [[("a", 1), ("b", 2)], {"a": 1, "b": 2}],
            [(("a", 1), ("b", 2)), {"a": 1, "b": 2}],
            [{"a": 1, "b": 2}, {"a": 1, "b": 2}],
            [None, {}],
        ],
    )
    def test_parse_counts(self, input, expected):
        assert parse_counts(input) == expected
