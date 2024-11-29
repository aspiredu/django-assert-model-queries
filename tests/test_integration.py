from textwrap import dedent
from unittest.mock import Mock

import pytest
from django.db.models import Count

from django_assert_model_queries import AssertModelNumQueriesContext
from django_assert_model_queries.patch import query_counts, reset_query_counter, patch_sql_compilers_for_debugging

from tests.testapp.models import Community


class TestPatching:
    @pytest.fixture
    def patch(self):
        unpatch = patch_sql_compilers_for_debugging()
        reset_query_counter()
        yield
        unpatch()
        reset_query_counter()

    @pytest.mark.parametrize(
        "using_db", ["default", "mysql"], ids=["sqlite", "mysql"]
    )
    @pytest.mark.django_db(databases=['default', 'mysql'])
    def test_unpatched_compilers(self, using_db):
        Community.objects.using(using_db).create(name="test")
        Community.objects.using(using_db).update(name="new")
        Community.objects.using(using_db).get(name="new")
        Community.objects.using(using_db).aggregate(count=Count("id"))
        Community.objects.using(using_db).all().delete()
        assert query_counts.get() == {}

    @pytest.mark.parametrize(
        "using_db", ["default", "mysql"], ids=["sqlite", "mysql"]
    )
    @pytest.mark.django_db(databases=['default', 'mysql'])
    def test_patched_compilers(self, using_db, patch):
        Community.objects.using(using_db).create(name="test")
        Community.objects.using(using_db).update(name="new")
        Community.objects.using(using_db).get(name="new")
        Community.objects.using(using_db).aggregate(count=Count("id"))
        assert query_counts.get() == {"testapp.Community": 4}
        Community.objects.using(using_db).all().delete()
        assert query_counts.get() == {"testapp.Community": 6, "testapp.Chapter": 1, "testapp.Community_topics": 1}

class TestAssertModelNumQueriesContext:
    @pytest.fixture
    def assert_context(self):
        context = AssertModelNumQueriesContext(connection=Mock(queries=[{"sql": "SELECT * FROM testapp.community"}]))
        context.initial_queries = 0
        context.final_queries = 1
        return context

    @pytest.mark.django_db
    def test_call_expects_overrides_init(self):
        context = AssertModelNumQueriesContext({"testapp.Community": 0})
        with context({"testapp.Community": 1}):
            assert Community.objects.first() is None
            assert context.expected_model_counts == {"testapp.Community": 1}

    def test_failure_message(self, assert_context):
        assert assert_context.failure_message({"djangonaut.Space": 1}, {"django.Commons": 2}) == dedent(
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

